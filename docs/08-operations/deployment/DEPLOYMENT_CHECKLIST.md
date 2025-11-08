# Render Deployment Checklist

**Project:** ToolboxAI Solutions
**Target:** Render.com Production Deployment
**Estimated Time:** 30-45 minutes
**Estimated Cost:** ~$59/month

---

## Phase 1: Gather Credentials (15 minutes)

### ✅ Supabase Credentials (Already Configured!)

**Project:** jlesbkscprldariqcbvt (us-east-1)

Your Supabase is already configured with these values:

1. [x] **Project URL**: `https://jlesbkscprldariqcbvt.supabase.co`
2. [x] **Anon/Public key**: `sb_publishable_s9XplM0Sz75mQSZdAPwdSw__Gye2M1q`
3. [x] **Service role key**: Configured ✓
4. [x] **Database URL** (pooler, port 6543): Configured ✓
5. [x] **Storage bucket**: `toolboxai-uploads` (already created)

**Note:** All environment files have been updated with your cloud Supabase credentials.

---

### ✅ AI API Keys

5. [ ] **OpenAI**: https://platform.openai.com/api-keys
   - [ ] Create or copy existing API key (starts with `sk-proj-...`)

6. [ ] **Anthropic Claude**: https://console.anthropic.com/settings/keys
   - [ ] Create or copy existing API key (starts with `sk-ant-api03-...`)

7. [ ] **Google AI**: https://makersuite.google.com/app/apikey
   - [ ] Create or copy existing API key (starts with `AIzaSy...`)

**Template:** Lines 32-40

---

### ✅ Pusher Credentials

8. [ ] Go to https://dashboard.pusher.com
9. [ ] Select your app or create new one
10. [ ] Go to **App Keys** tab
    - [ ] Copy **app_id** (should be `2050003` if existing)
    - [ ] Copy **key** (20-character hex)
    - [ ] Copy **secret** (40-character hex)
    - [ ] Verify **cluster** is `us2`

**Template:** Lines 46-51

---

### ✅ Monitoring Services

11. [ ] **Sentry Backend** (already configured):
    ```
    https://6175c9912112e5a9fa094247539d13f5@o4509912543199232.ingest.us.sentry.io/4510294208937984
    ```

12. [ ] **Sentry Frontend**: https://sentry.io
    - [ ] Create new project for frontend (React)
    - [ ] Copy DSN (similar format to backend)

13. [ ] **Celery Flower Monitoring**:
    - [ ] Generate password: `openssl rand -base64 24`
    - [ ] Save as `FLOWER_BASIC_AUTH_PASSWORD`

**Template:** Lines 57-67

---

### ✅ Generate Security Tokens

14. [ ] Generate **JWT_SECRET_KEY**:
    ```bash
    openssl rand -hex 32
    ```

15. [ ] Generate **SECRET_KEY**:
    ```bash
    openssl rand -hex 32
    ```

16. [ ] Generate **ENCRYPTION_KEY**:
    ```bash
    openssl rand -hex 32
    ```

17. [ ] Verify all three are different (64 hex characters each)

**Template:** Lines 73-78

---

## Phase 2: Organize Configuration (10 minutes)

### ✅ Fill Configuration Template

18. [ ] Open: `infrastructure/render/ENVIRONMENT_VARIABLES.template`
19. [ ] Fill in ALL values marked `[REQUIRED]`
20. [ ] Fill in ALL values marked `[GENERATE]` with generated tokens
21. [ ] Verify no placeholders remain (search for `[REQUIRED]` and `[GENERATE]`)
22. [ ] Save filled template to secure location (password manager recommended)
23. [ ] **DO NOT** commit filled template to Git

---

### ✅ Validate Configuration

24. [ ] Run validation script:
    ```bash
    cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
    python scripts/validate_render_env.py
    ```

25. [ ] Review validation results:
    - [ ] All required variables show ✓ OK
    - [ ] No ✗ Failed items
    - [ ] Address any ⚠ Warnings if possible

26. [ ] If validation fails:
    - [ ] Review error messages
    - [ ] Fix identified issues
    - [ ] Re-run validation
    - [ ] Repeat until all checks pass

---

## Phase 3: Deploy to Render (15 minutes)

### ✅ Create Blueprint Instance

27. [ ] Go to https://dashboard.render.com
28. [ ] Click **Blueprints** in left sidebar
29. [ ] Click **New Blueprint Instance**
30. [ ] Connect GitHub account if not already connected
31. [ ] Repository: Select **GrayGhostDev/ToolboxAI-Solutions**
32. [ ] Branch: **main**
33. [ ] Blueprint path: Verify shows `infrastructure/render/render.production.yaml`
34. [ ] Click **Apply**

---

### ✅ Configure Environment Variable Groups

Render will prompt you to configure 4 environment variable groups:

#### Group 1: toolboxai-secrets

35. [ ] Set all Supabase values (URL, keys, DATABASE_URL)
36. [ ] Set all AI API keys (OpenAI, Anthropic, Google)
37. [ ] Set all Pusher values (APP_ID, KEY, SECRET, CLUSTER)
38. [ ] Set Sentry backend DSN
39. [ ] Set all security tokens (JWT_SECRET_KEY, SECRET_KEY, ENCRYPTION_KEY)
40. [ ] Set application config (ENVIRONMENT=production, LOG_LEVEL=INFO, DEBUG=false)
41. [ ] Set CORS_ORIGINS to: `["https://toolboxai-dashboard.onrender.com"]`

#### Group 2: toolboxai-frontend-env

42. [ ] Set `VITE_API_BASE_URL=https://toolboxai-backend.onrender.com`
43. [ ] Set `VITE_PUSHER_KEY` (same as PUSHER_KEY from Group 1)
44. [ ] Set `VITE_PUSHER_CLUSTER=us2`
45. [ ] Set `VITE_SENTRY_DSN` (frontend Sentry DSN from step 12)
46. [ ] Set `VITE_APP_NAME=ToolboxAI Solutions`
47. [ ] Set `VITE_APP_VERSION=1.0.0`

#### Group 3: toolboxai-monitoring

48. [ ] Generate Grafana password: `openssl rand -base64 24`
49. [ ] Set `GRAFANA_ADMIN_USERNAME=admin`
50. [ ] Set `GRAFANA_ADMIN_PASSWORD` (from step 48)
51. [ ] Set `PROMETHEUS_RETENTION_TIME=15d`
52. [ ] Set `LOKI_RETENTION_PERIOD=30d`
53. [ ] Set `ALERTMANAGER_SLACK_WEBHOOK_URL` (optional, leave empty if not using Slack)

#### Group 4: supabase-local

54. [ ] Copy all values from `.env.supabase.local.example`
55. [ ] These are for local development only, not used in production
56. [ ] Use the default values from the template (lines 114-128)

---

### ✅ Review and Deploy

57. [ ] Review service summary:
    - [ ] 7 Starter services ($7 each = $49)
    - [ ] 1 Starter Redis ($10)
    - [ ] 1 Free static site
    - [ ] 1 Free cron job
    - [ ] **Total: ~$59/month**

58. [ ] Click **Apply** to start deployment

59. [ ] Wait for deployment (typically 5-10 minutes)
    - [ ] Backend building...
    - [ ] Redis starting...
    - [ ] Dashboard building...
    - [ ] Workers starting...

---

## Phase 4: Verify Deployment (10 minutes)

### ✅ Check Service Health

60. [ ] **Backend API**: https://toolboxai-backend.onrender.com/health
    - [ ] Status: `200 OK`
    - [ ] Response: `{"status": "healthy", "database": "connected"}`

61. [ ] **Dashboard**: https://toolboxai-dashboard.onrender.com
    - [ ] Site loads successfully
    - [ ] No console errors (open browser DevTools)

62. [ ] **MCP API**: https://toolboxai-mcp.onrender.com/health
    - [ ] Status: `200 OK`

63. [ ] **Agent Coordinator**: https://toolboxai-agent-coordinator.onrender.com/health
    - [ ] Status: `200 OK`

64. [ ] **Celery Flower**: https://toolboxai-celery-flower.onrender.com
    - [ ] Prompts for basic auth (username: `admin`, password from step 13)
    - [ ] Dashboard loads showing worker status

---

### ✅ Check Logs

65. [ ] In Render Dashboard, go to **toolboxai-backend** service
66. [ ] Click **Logs** tab
67. [ ] Verify you see:
    - [ ] `✅ Database connection successful`
    - [ ] `Server started successfully`
    - [ ] No error messages

68. [ ] Check **toolboxai-celery-worker** logs:
    - [ ] `[INFO/MainProcess] Connected to redis://...`
    - [ ] `[INFO/MainProcess] celery@... ready.`

69. [ ] Check **toolboxai-celery-beat** logs:
    - [ ] `[INFO/MainProcess] beat: Starting...`
    - [ ] Scheduled tasks listed

---

### ✅ Test Key Features

70. [ ] **Authentication**:
    - [ ] Can access login page
    - [ ] Try registering new user (optional)
    - [ ] Try logging in (optional)

71. [ ] **Database Connection**:
    - [ ] Backend health check shows `database: connected`
    - [ ] No database errors in logs

72. [ ] **Real-time Features** (if applicable):
    - [ ] Test any real-time updates using Pusher
    - [ ] Check browser console for Pusher connection

73. [ ] **File Upload** (if applicable):
    - [ ] Test file upload to Supabase Storage
    - [ ] Verify file appears in Supabase Dashboard → Storage

---

## Phase 5: Post-Deployment (Optional)

### ✅ Custom Domain (Optional)

74. [ ] In Render Dashboard, go to **toolboxai-dashboard** service
75. [ ] Click **Settings** → **Custom Domain**
76. [ ] Add your domain (e.g., `app.toolboxai.com`)
77. [ ] Add DNS records as instructed by Render
78. [ ] Update `VITE_API_BASE_URL` if backend also has custom domain
79. [ ] Update `CORS_ORIGINS` in backend to include custom domain

---

### ✅ Monitoring Setup

80. [ ] **Sentry**: https://sentry.io
    - [ ] Verify backend project receiving events
    - [ ] Verify frontend project receiving events
    - [ ] Set up alert rules (optional)

81. [ ] **Grafana**: https://toolboxai-monitoring.onrender.com (if exposed)
    - [ ] Login with Grafana credentials (step 48-49)
    - [ ] Explore dashboards
    - [ ] Set up alerts (optional)

82. [ ] **Celery Flower**: https://toolboxai-celery-flower.onrender.com
    - [ ] Monitor task queues
    - [ ] Verify tasks being processed

---

### ✅ Security Hardening

83. [ ] Review Supabase Row Level Security (RLS) policies:
    - [ ] Go to Supabase Dashboard → Authentication → Policies
    - [ ] Verify RLS enabled on all tables
    - [ ] Test policies with different user roles

84. [ ] Enable database backups:
    - [ ] Supabase Dashboard → Database → Backups
    - [ ] Verify daily backups enabled
    - [ ] Consider enabling Point-in-Time Recovery

85. [ ] Set up additional monitoring:
    - [ ] Configure Slack alerts in Alertmanager (optional)
    - [ ] Set up uptime monitoring (optional)

---

## Troubleshooting

### Database Connection Issues

**Symptom:** `connection refused` or `timeout`

- [ ] Verify DATABASE_URL uses port **6543** (pooler) not 5432
- [ ] Check password doesn't contain special characters needing URL encoding
- [ ] Test connection string in local `psql` or database client

**Symptom:** `relation does not exist`

- [ ] Run database migrations (see `docs/DATABASE_MIGRATION.md`)
- [ ] Verify tables exist in Supabase Dashboard → Table Editor

---

### Celery Not Working

**Symptom:** Tasks not processing

- [ ] Check Redis connection in worker logs
- [ ] Verify REDIS_URL set correctly (should be automatic)
- [ ] Restart celery-worker service in Render

**Symptom:** Beat not scheduling

- [ ] Check celery-beat logs for errors
- [ ] Verify timezone configuration (should be UTC)

---

### Frontend Issues

**Symptom:** CORS errors in browser console

- [ ] Verify CORS_ORIGINS includes dashboard URL
- [ ] Check backend service is running
- [ ] Verify VITE_API_BASE_URL points to correct backend

**Symptom:** Blank page or loading indefinitely

- [ ] Check browser console for JavaScript errors
- [ ] Verify frontend build completed successfully (check logs)
- [ ] Check static file paths are correct

---

### File Upload Issues

**Symptom:** Upload fails

- [ ] Verify `toolboxai-uploads` bucket exists in Supabase
- [ ] Check bucket permissions (public vs private)
- [ ] Verify SUPABASE_SERVICE_ROLE_KEY set correctly
- [ ] Check storage logs in Supabase Dashboard

---

## Success Criteria

- [ ] All 10 services deployed successfully
- [ ] All health checks returning 200 OK
- [ ] No errors in service logs
- [ ] Database connection working
- [ ] Frontend loads successfully
- [ ] Authentication working (if tested)
- [ ] Real-time features working (if applicable)
- [ ] File uploads working (if tested)
- [ ] Monitoring and error tracking active

---

## Documentation Reference

- **Full Deployment Guide**: `docs/RENDER_DEPLOYMENT_GUIDE.md`
- **Environment Template**: `infrastructure/render/ENVIRONMENT_VARIABLES.template`
- **Blueprint File**: `infrastructure/render/render.production.yaml`
- **Validation Script**: `scripts/validate_render_env.py`
- **Supabase Local Setup**: `docs/SUPABASE_LOCAL_SETUP.md`

---

## Support Resources

- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Render Status**: https://status.render.com
- **Supabase Status**: https://status.supabase.com

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Production URL:** https://toolboxai-dashboard.onrender.com
**Backend URL:** https://toolboxai-backend.onrender.com

---

*Keep this checklist for future reference and disaster recovery procedures.*
