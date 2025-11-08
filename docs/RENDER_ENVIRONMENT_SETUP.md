# Render Environment Groups Setup Guide

## Quick Fix for Failed Blueprint Deployments

**Issue**: All blueprint services failed because environment groups were not created/linked.

**Solution**: Follow this 3-step process to create and link environment groups.

---

## Step 1: Create Environment Groups in Render Dashboard

### 1a. Create `toolboxai-secrets` Group

1. Go to: https://dashboard.render.com/env-groups
2. Click **"New Environment Group"**
3. Name: `toolboxai-secrets`
4. Click **"Add from .env"** button
5. Paste the following 39 variables from your local `.env` file:

```bash
# === CRITICAL VARIABLES (25 with real values) ===

# AI/ML API Keys
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=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
REPLICATE_API_TOKEN=r8_DlSYrrAzQrQHl6TyPhQ2gXd4nR0skzK4URqVp

# LangChain/LangSmith
LANGCHAIN_API_KEY=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
LANGCHAIN_PROJECT_ID=3e8ad997-5252-40cd-abe3-b70e9439a811
LANGCHAIN_PROJECT=ToolboxAI-Solutions
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# LangCache (Semantic Caching)
LANGCACHE_API_KEY=wy4ECQMIVTKLbf4DoKjgl1DyOqSaI36fvrh9DOOxBNrYQup6xUcrhk9nBNFEqHlw0oIBiHkP8QGv6KkR9g9rK8R1x8WbNvxZqxuZ8KGvpk80LdhXQAyRXoE1EJtlGicLd1DqSJeRJvBQ7Eu6m9Or8ovEcwrqq1n216DAMNSIcIF-hA586GEjhOb6GOOwdnQlY1eAs83-5EP33IPJGn-gJ1n0By6RA93-WPM8vjvRdMjO_Ija
LANGCACHE_CACHE_ID=f5c5e531f8954e35b864eb710d3f891c
LANGCACHE_API_BASE_URL=https://gcp-us-east4.langcache.redis.io
LANGCACHE_SERVER_URL=https://gcp-us-east4.langcache.redis.io
LANGCACHE_ENABLED=true

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_3ArqrdCHHmjxHvgtAt2zxr2Znd8L8ziEWUiH8NDI49
CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
CLERK_WEBHOOK_SIGNING_SECRET=whsec_yfJVjj0muO9lOYGyOEMH3cbVBXS7Znct
CLERK_JWKS_URL=https://casual-firefly-39.clerk.accounts.dev/.well-known/jwks.json

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://dbuser_4qnrmosa:13y70agAhh2LSyjLw3LYtF1kRPra0qnNhdQcng6YNb0lMz5h@postgres:5432/toolboxai_6rmgje4u
SUPABASE_DATABASE_URL=postgresql://postgres:ToolBoXA1!2025!@db.jlesbkscprldariqcbvt.supabase.co:6543/postgres?sslmode=require

# Supabase Cloud Configuration
SUPABASE_URL=https://jlesbkscprldariqcbvt.supabase.co
SUPABASE_ANON_KEY=sb_publishable_s9XplM0Sz75mQSZdAPwdSw__Gye2M1q
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZXNia3NjcHJsZGFyaXFjYnZ0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODQzNjM1NiwiZXhwIjoyMDc0MDEyMzU2fQ.J_4amgJXEoHY3yhJpHAcKP7X-vnSBPOFCee626k8ZlI
SUPABASE_STORAGE_BUCKET=toolboxai-uploads

# Supabase S3-Compatible Storage
SUPABASE_S3_ENDPOINT=https://jlesbkscprldariqcbvt.storage.supabase.co/storage/v1/s3
SUPABASE_S3_REGION=us-east-2
SUPABASE_S3_ACCESS_KEY_ID=e31a9fa3a7de8a46021afd11f7ca70ba
SUPABASE_S3_SECRET_ACCESS_KEY=da49278f913569ad3f344caad0f17b2d2f1f2dae5633dae2a1e2bdc9ae3e157c

# Redis Cloud (Production)
REDIS_CLOUD_PASSWORD=48719c4f1003276662b34cd5bd39a46c2d1ae98478f71bc3b34ebb3033e22d40

# Security Keys
JWT_SECRET_KEY=aead63acfdc889f3d1c34a1d8b47dad41e7d6c9c0c7487863c5c14a207b90a3e
SESSION_SECRET=2ff561574a94aeb0d0fd1e16be4d11c7da7fa8b3582f3357b5bb996dd3c79985
ENCRYPTION_KEY=f5d80bd450d5154e9fc2f85f2c1da12cad2bcc7e2efab0631cc3ec65150c7747

# Email Service (SendGrid)
SENDGRID_API_KEY=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
SENDGRID_FROM_EMAIL=curtis@grayghostdata.com

# SMS/Voice (Twilio)
TWILIO_ACCOUNT_SID=AC554c2d9641861cbd82d7c4db296fd189
TWILIO_AUTH_TOKEN=febcac24ce956f1942069ba7356e5a0c

# Real-time (Pusher)
PUSHER_APP_ID=2050003
PUSHER_KEY=73f059a21bb304c7d68c
PUSHER_SECRET=fe8d15d3d7ee36652b7a
PUSHER_CLUSTER=us2

# Monitoring (Sentry)
SENTRY_DSN=https://6175c9912112e5a9fa094247539d13f5@o4509912543199232.ingest.us.sentry.io/4510294208937984

# === OPTIONAL PLACEHOLDERS (14 - configure as needed) ===
GOOGLE_AI_API_KEY=PLACEHOLDER_GOOGLE_AI_API_KEY_NEEDS_CONFIGURATION
COHERE_API_KEY=PLACEHOLDER_COHERE_API_KEY_OPTIONAL
HUGGINGFACE_API_KEY=PLACEHOLDER_HUGGINGFACE_API_KEY_OPTIONAL
STABILITY_API_KEY=PLACEHOLDER_STABILITY_API_KEY_OPTIONAL
DEEPGRAM_API_KEY=PLACEHOLDER_DEEPGRAM_API_KEY_OPTIONAL
ELEVENLABS_API_KEY=PLACEHOLDER_ELEVENLABS_API_KEY_OPTIONAL
PERPLEXITY_API_KEY=PLACEHOLDER_PERPLEXITY_API_KEY_OPTIONAL
AWS_ACCESS_KEY_ID=PLACEHOLDER_AWS_ACCESS_KEY_ID_OPTIONAL
AWS_SECRET_ACCESS_KEY=PLACEHOLDER_AWS_SECRET_ACCESS_KEY_OPTIONAL
AWS_REGION=PLACEHOLDER_AWS_REGION_OPTIONAL
GITHUB_PAT_TOKEN=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
RENDER_API_KEY=rnd_Xv0q1Yz7W2bvWz9kwMbMXb1hAUif
TEAMCITY_PIPELINE_ACCESS_TOKEN=eyJ0eXAiOiAiVENWMiJ9.Z00zSzRFazBrNktpandnemRUZ2dJRGhBbVlF.MTZhZjcxM2EtZWJiZC00ODA2LTgxMmQtMzA2MWZjMjk2OWYz
ROBLOX_API_KEY=your_roblox_api_key_here
```

6. Click **"Create Environment Group"**

---

### 1b. Create `toolboxai-frontend-env` Group

1. Click **"New Environment Group"**
2. Name: `toolboxai-frontend-env`
3. Add these 12 variables:

```bash
# Supabase Frontend
VITE_SUPABASE_URL=https://jlesbkscprldariqcbvt.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_s9XplM0Sz75mQSZdAPwdSw__Gye2M1q
VITE_SUPABASE_S3_ENDPOINT=https://jlesbkscprldariqcbvt.storage.supabase.co/storage/v1/s3
VITE_SUPABASE_S3_REGION=us-east-2

# Clerk Frontend
VITE_CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
VITE_CLERK_FRONTEND_API_URL=https://casual-firefly-39.clerk.accounts.dev
VITE_ENABLE_CLERK_AUTH=true
VITE_CLERK_SIGN_IN_URL=/sign-in
VITE_CLERK_SIGN_UP_URL=/sign-up
VITE_CLERK_AFTER_SIGN_IN_URL=/dashboard
VITE_CLERK_AFTER_SIGN_UP_URL=/dashboard

# Pusher Frontend
VITE_PUSHER_KEY=73f059a21bb304c7d68c
VITE_PUSHER_CLUSTER=us2
VITE_ENABLE_PUSHER=true
```

4. Click **"Create Environment Group"**

---

### 1c. Create `toolboxai-monitoring` Group

1. Click **"New Environment Group"**
2. Name: `toolboxai-monitoring`
3. Add these 5 variables (all optional):

```bash
ALERT_WEBHOOK_URL=PLACEHOLDER_ALERT_WEBHOOK_URL_OPTIONAL
SLACK_WEBHOOK_URL=PLACEHOLDER_SLACK_WEBHOOK_URL_OPTIONAL
DISCORD_WEBHOOK_URL=PLACEHOLDER_DISCORD_WEBHOOK_URL_OPTIONAL
PAGERDUTY_INTEGRATION_KEY=PLACEHOLDER_PAGERDUTY_INTEGRATION_KEY_OPTIONAL
GRAFANA_API_KEY=PLACEHOLDER_GRAFANA_API_KEY_OPTIONAL
```

4. Click **"Create Environment Group"**

---

## Step 2: Link Environment Groups to Services

Now that groups are created, link them to each service:

### 2a. Link toolboxai-secrets to Backend Services

For each of these services:
- `toolboxai-backend`
- `toolboxai-mcp`
- `toolboxai-agent-coordinator`
- `toolboxai-celery-worker`
- `toolboxai-celery-beat`
- `toolboxai-celery-flower`
- `toolboxai-cleanup`

**Steps:**
1. Go to Service → Environment tab
2. Click "Link Environment Group"
3. Select `toolboxai-secrets`
4. Click "Link Group"

### 2b. Dashboard (Hosted on Vercel)

**Note:** `toolboxai-dashboard` is hosted on Vercel, not Render. No environment group linking needed for Render.
Configure environment variables directly in Vercel dashboard: https://vercel.com/dashboard

### 2c. Link toolboxai-monitoring to Monitoring Service

For `toolboxai-monitoring`:
1. Go to Service → Environment tab
2. Click "Link Environment Group"
3. Select `toolboxai-monitoring`
4. Click "Link Group"

---

## Step 3: Trigger Redeployment

After all groups are linked:

**Option 1: Manual Redeploy (Recommended)**
1. Go to each failed service
2. Click "Manual Deploy" → "Deploy latest commit"
3. Wait for builds to complete (~5-10 minutes each)

**Option 2: Git Push (Triggers all services)**
```bash
# Make a small change to trigger redeployment
git commit --allow-empty -m "trigger: redeploy with environment groups"
git push origin main
```

---

## Verification

After redeployment, verify services are running:

```bash
# Backend health check
curl https://toolboxai-backend.onrender.com/health

# Dashboard (Hosted on Vercel)
curl https://toolboxai-dashboard.vercel.app

# MCP Server
curl https://toolboxai-mcp.onrender.com/health

# Celery Flower UI
curl https://toolboxai-celery-flower.onrender.com
```

---

## Automated Helper Script

Run this script to verify environment groups are properly linked:

```bash
python3 scripts/verify_render_setup.py
```

---

## Troubleshooting

### Issue: Services still failing after linking groups

**Check:**
1. Verify group is actually linked: Service → Environment → Should show linked group
2. Check placeholder values: Some variables may need real values instead of `PLACEHOLDER_*`
3. View build logs: Look for specific missing environment variables

### Issue: Can't find environment groups

**Solution:**
- Groups are workspace-specific
- Ensure you're in the correct Render workspace
- Navigate to: https://dashboard.render.com/env-groups

### Issue: Build succeeds but service crashes

**Check:**
1. Service logs for runtime errors
2. Database connectivity: `DATABASE_URL` must be accessible from Render
3. Redis connectivity: May need to update `REDIS_URL` for Render's Redis service

---

## Quick Reference: Service → Environment Group Mapping

| Service | Environment Group | Required |
|---------|------------------|----------|
| toolboxai-backend | toolboxai-secrets | ✅ Yes |
| toolboxai-mcp | toolboxai-secrets | ✅ Yes |
| toolboxai-agent-coordinator | toolboxai-secrets | ✅ Yes |
| toolboxai-celery-worker | toolboxai-secrets | ✅ Yes |
| toolboxai-celery-beat | toolboxai-secrets | ✅ Yes |
| toolboxai-celery-flower | toolboxai-secrets | ✅ Yes |
| toolboxai-cleanup | toolboxai-secrets | ✅ Yes |
| toolboxai-dashboard | (hosted on Vercel) | N/A |
| toolboxai-monitoring | toolboxai-monitoring | ⚠️ Optional |
| toolboxai-redis | (none - managed service) | N/A |

---

**Next**: Once all services are deployed successfully, configure custom domains and SSL certificates.
