# Render API Configuration Guide
**Purpose:** Comprehensive guide for configuring Render environment variables
**Status:** API limitations identified - hybrid approach recommended

---

## 📋 Executive Summary

**Discovery:** Render API v1 has limitations for bulk environment variable group updates:
- ✅ `GET /env-groups` - List groups (works)
- ✅ `POST /env-groups` - Create groups (works)
- ❌ `PUT /env-groups/{id}` - Bulk update (405 Method Not Allowed)
- ❌ `PATCH /env-groups/{id}` - Bulk update (405 Method Not Allowed)

**Recommended Approach:** Hybrid configuration using Dashboard + API

---

## 🎯 Configuration Status

### Variables Ready
- **Total Variables:** 56
- **Real Values (from .env):** 31 (54.4%)
- **Placeholders (optional):** 25 (45.6%)

### Critical Variables (31 found)
✅ **Authentication:** Clerk (4 vars)
✅ **Database:** Supabase (8 vars)
✅ **AI/ML:** OpenAI, Anthropic, LangChain (6 vars)
✅ **Real-time:** Pusher (3 vars)
✅ **Monitoring:** Sentry (1 var)
✅ **Email/SMS:** SendGrid, Twilio (3 vars)
✅ **Frontend:** Vite environment vars (6 vars)

### Optional Variables (25 placeholders)
⚠️ **Payment:** Stripe (3 vars)
⚠️ **Cloud Storage:** AWS S3 (3 vars)
⚠️ **Additional AI:** Google AI (1 var)
⚠️ **Monitoring:** Datadog, New Relic (2 vars)
⚠️ **Analytics:** Google Analytics, Hotjar, Mixpanel, Intercom (6 vars)
⚠️ **Webhooks:** Slack, Discord, PagerDuty (5 vars)
⚠️ **Other:** GitHub, GCP, Flower auth (5 vars)

---

## 🚀 Recommended Configuration Method

### Method 1: Render Dashboard (Fastest - Recommended)

**Estimated Time:** 15-20 minutes

#### Step 1: Prepare Environment File for Import

Create a file with only the critical variables for easy import:

```bash
# Create import-ready file
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Generate critical variables only
python3 scripts/configure_render_env.py --no-placeholders --dry-run > /tmp/render_vars_preview.txt

# Or manually create render-import.env with critical values
cat > render-import.env << 'EOF'
# Backend Secrets (toolboxai-secrets group)
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=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
REPLICATE_API_TOKEN=r8_DlSYrrAzQrQHl6TyPhQ2gXd4nR0skzK4URqVp
LANGCHAIN_API_KEY=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
LANGCACHE_API_KEY=wy4ECQMIVTKLbf4DoKjgl1DyOqSaI36fvrh9DOOxBNrYQup6xUcrhk9nBNFEqHlw0oIBiHkP8QGv6KkR9g9rK8R1x8WbNvxZqxuZ8KGvpk80LdhXQAyRXoE1EJtlGicLd1DqSJeRJvBQ7Eu6m9Or8ovEcwrqq1n216DAMNSIcIF-hA586GEjhOb6GOOwdnQlY1eAs83-5EP33IPJGn-gJ1n0By6RA93-WPM8vjvRdMjO_Ija
LANGCACHE_CACHE_ID=f5c5e531f8954e35b864eb710d3f891c
CLERK_SECRET_KEY=sk_test_3ArqrdCHHmjxHvgtAt2zxr2Znd8L8ziEWUiH8NDI49
CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
CLERK_WEBHOOK_SIGNING_SECRET=whsec_yfJVjj0muO9lOYGyOEMH3cbVBXS7Znct
CLERK_JWKS_URL=https://casual-firefly-39.clerk.accounts.dev/.well-known/jwks.json
DATABASE_URL=postgresql://postgres:ToolBoXA1!2025!@db.jlesbkscprldariqcbvt.supabase.co:6543/postgres?sslmode=require
SUPABASE_URL=https://jlesbkscprldariqcbvt.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZXNia3NjcHJsZGFyaXFjYnZ0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODQzNjM1NiwiZXhwIjoyMDc0MDEyMzU2fQ.J_4amgJXEoHY3yhJpHAcKP7X-vnSBPOFCee626k8ZlI
SUPABASE_DATABASE_URL=postgresql://postgres:ToolBoXA1!2025!@db.jlesbkscprldariqcbvt.supabase.co:6543/postgres?sslmode=require
SUPABASE_S3_ENDPOINT=https://jlesbkscprldariqcbvt.storage.supabase.co/storage/v1/s3
SUPABASE_S3_REGION=us-east-2
SUPABASE_S3_ACCESS_KEY_ID=e31a9fa3a7de8a46021afd11f7ca70ba
SUPABASE_S3_SECRET_ACCESS_KEY=da49278f913569ad3f344caad0f17b2d2f1f2dae5633dae2a1e2bdc9ae3e157c
PUSHER_APP_ID=2050003
PUSHER_KEY=73f059a21bb304c7d68c
PUSHER_SECRET=fe8d15d3d7ee36652b7a
SENTRY_DSN=https://6175c9912112e5a9fa094247539d13f5@o4509912543199232.ingest.us.sentry.io/4510294208937984
SENDGRID_API_KEY=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
TWILIO_ACCOUNT_SID=AC554c2d9641861cbd82d7c4db296fd189
TWILIO_AUTH_TOKEN=febcac24ce956f1942069ba7356e5a0c

# Frontend Variables (toolboxai-frontend-env group)
VITE_SUPABASE_URL=https://jlesbkscprldariqcbvt.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_s9XplM0Sz75mQSZdAPwdSw__Gye2M1q
VITE_SUPABASE_S3_ENDPOINT=https://jlesbkscprldariqcbvt.storage.supabase.co/storage/v1/s3
VITE_CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
VITE_CLERK_FRONTEND_API_URL=https://casual-firefly-39.clerk.accounts.dev
VITE_PUSHER_KEY=73f059a21bb304c7d68c
EOF
```

#### Step 2: Configure via Render Dashboard

1. **Navigate to Dashboard:**
   ```
   https://dashboard.render.com/env-groups
   ```

2. **Configure `toolboxai-secrets` group:**
   - Click on "toolboxai-secrets" environment group
   - Click "Add from .env" button
   - Paste contents from `render-import.env` (backend section)
   - Click "Save Changes"

3. **Configure `toolboxai-frontend-env` group:**
   - Click on "toolboxai-frontend-env" environment group
   - Click "Add from .env" button
   - Paste frontend variables from `render-import.env`
   - Click "Save Changes"

4. **Trigger Deployments:**
   - Go to each service
   - Click "Manual Deploy" → "Deploy latest commit"
   - Or wait for auto-deploy if enabled

#### Step 3: Verify Configuration

Check service logs:
```bash
render logs toolboxai-backend --tail 50
render logs toolboxai-dashboard --tail 50
```

---

### Method 2: Individual API Updates (For Future Changes)

While bulk updates aren't supported, individual variable updates work:

```python
import os
import requests

API_KEY = os.getenv('RENDER_API_KEY')
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Update single environment variable in a group
group_id = "evg-d479opq4d50c73813bu0"  # toolboxai-secrets

# This works for individual updates
response = requests.put(
    f"https://api.render.com/v1/env-groups/{group_id}/env-vars/OPENAI_API_KEY",
    headers=headers,
    json={"value": "new-api-key-value"}
)
```

**Use Cases:**
- Rotating API keys
- Updating single credentials
- Automated credential rotation scripts

---

### Method 3: Service-Level Environment Variables (Alternative)

If environment groups don't work well, configure directly on services:

```bash
# Get service ID
render services --output json | jq '.[] | select(.service.name=="toolboxai-backend") | .service.id'

# Add environment variable to specific service
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key":"OPENAI_API_KEY","value":"sk-..."}' \
  https://api.render.com/v1/services/{service_id}/env-vars
```

**Pros:**
- Full API support
- Scriptable
- Service-specific configuration

**Cons:**
- Must configure each service individually
- No shared configuration across services
- More maintenance overhead

---

## 🔧 Script Usage Reference

### Dry Run (Preview Changes)
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Preview all variables
python3 scripts/configure_render_env.py --dry-run

# Preview only real values (skip placeholders)
python3 scripts/configure_render_env.py --dry-run --no-placeholders

# Preview specific group
python3 scripts/configure_render_env.py --dry-run --group toolboxai-secrets

# Debug mode (show API responses)
python3 scripts/configure_render_env.py --dry-run --debug
```

### Configuration (When API Supports Bulk Updates)
```bash
# Configure all variables
python3 scripts/configure_render_env.py

# Configure only real values
python3 scripts/configure_render_env.py --no-placeholders

# Configure and deploy
python3 scripts/configure_render_env.py --no-placeholders --deploy
```

---

## 📊 Environment Variable Mapping

### toolboxai-secrets (25 critical variables)

| Category | Variables | Status |
|----------|-----------|--------|
| **AI/ML APIs** | OPENAI_API_KEY, ANTHROPIC_API_KEY, REPLICATE_API_TOKEN | ✅ Ready |
| **LangChain** | LANGCHAIN_API_KEY, LANGCACHE_API_KEY, LANGCACHE_CACHE_ID | ✅ Ready |
| **Authentication** | CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY, CLERK_WEBHOOK_SIGNING_SECRET, CLERK_JWKS_URL | ✅ Ready |
| **Database** | DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DATABASE_URL | ✅ Ready |
| **Storage** | SUPABASE_S3_ENDPOINT, SUPABASE_S3_REGION, SUPABASE_S3_ACCESS_KEY_ID, SUPABASE_S3_SECRET_ACCESS_KEY | ✅ Ready |
| **Real-time** | PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET | ✅ Ready |
| **Monitoring** | SENTRY_DSN | ✅ Ready |
| **Email** | SENDGRID_API_KEY | ✅ Ready |
| **SMS** | TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN | ✅ Ready |

### toolboxai-frontend-env (6 critical variables)

| Variable | Purpose | Status |
|----------|---------|--------|
| VITE_SUPABASE_URL | Supabase API endpoint | ✅ Ready |
| VITE_SUPABASE_ANON_KEY | Public Supabase key | ✅ Ready |
| VITE_SUPABASE_S3_ENDPOINT | S3-compatible storage | ✅ Ready |
| VITE_CLERK_PUBLISHABLE_KEY | Clerk public key | ✅ Ready |
| VITE_CLERK_FRONTEND_API_URL | Clerk API endpoint | ✅ Ready |
| VITE_PUSHER_KEY | Pusher public key | ✅ Ready |

### toolboxai-monitoring (0 critical, 5 optional)

All placeholder values - configure later as needed:
- ALERT_WEBHOOK_URL
- SLACK_WEBHOOK_URL
- DISCORD_WEBHOOK_URL
- PAGERDUTY_INTEGRATION_KEY
- GRAFANA_API_KEY

---

## ✅ Post-Configuration Checklist

After configuring environment variables:

### 1. Verify Services Start
```bash
render services --output json | jq '.[] | {name: .service.name, status: .service.serviceDetails.state}'
```

### 2. Check Health Endpoints
```bash
# Backend
curl https://toolboxai-backend.onrender.com/health

# Expected response:
# {"status": "healthy", "database": "connected", "redis": "connected"}

# Dashboard
curl https://toolboxai-dashboard.onrender.com

# Expected: HTML content
```

### 3. Test Authentication
```bash
# Test Clerk authentication
curl -X POST https://toolboxai-backend.onrender.com/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "test-token"}'
```

### 4. Test Database Connectivity
```bash
# View backend logs for database connection
render logs toolboxai-backend --tail 100 | grep -i "database\|supabase"

# Should see: "Connected to database" or similar
```

### 5. Test S3 Storage
```bash
# Test file upload endpoint
curl -X POST https://toolboxai-backend.onrender.com/api/v1/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.txt"

# Should return: {"status": "success", "url": "https://..."}
```

### 6. Monitor Service Health
```bash
# Watch all service logs
render logs toolboxai-backend --tail 20 &
render logs toolboxai-dashboard --tail 20 &
render logs toolboxai-mcp --tail 20 &
```

---

## 🔄 Updating Environment Variables

### Via Dashboard (Recommended)
1. Navigate to https://dashboard.render.com/env-groups
2. Select environment group
3. Update variables
4. Click "Save Changes"
5. Services auto-redeploy with new values

### Via Script (Individual Variables)
Create `update_single_var.py`:
```python
#!/usr/bin/env python3
import os
import sys
import requests

API_KEY = os.getenv('RENDER_API_KEY')
GROUP_ID = sys.argv[1]  # e.g., evg-d479opq4d50c73813bu0
VAR_NAME = sys.argv[2]   # e.g., OPENAI_API_KEY
VAR_VALUE = sys.argv[3]  # New value

response = requests.put(
    f"https://api.render.com/v1/env-groups/{GROUP_ID}/env-vars/{VAR_NAME}",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={"value": VAR_VALUE}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

Usage:
```bash
python3 update_single_var.py evg-d479opq4d50c73813bu0 OPENAI_API_KEY "new-key-value"
```

---

## 🐛 Troubleshooting

### Issue: 405 Method Not Allowed
**Symptom:** API returns 405 when trying to bulk update env groups

**Cause:** Render API doesn't support bulk environment variable updates via PUT/PATCH

**Solution:** Use Render Dashboard for bulk configuration

### Issue: Variables Not Updating
**Symptom:** Changed variables but services still use old values

**Cause:** Services need to be redeployed to pick up new environment variables

**Solution:**
```bash
# Trigger manual deploy
render deploys create --service toolboxai-backend

# Or via dashboard: Manual Deploy → Deploy latest commit
```

### Issue: Service Fails to Start
**Symptom:** Service shows "Build failed" or "Deploy failed"

**Cause:** Missing required environment variable

**Solution:**
1. Check service logs: `render logs toolboxai-backend --tail 100`
2. Look for errors like "OPENAI_API_KEY not set"
3. Add missing variable via dashboard
4. Redeploy

---

## 📝 Summary

**Current Status:**
- ✅ Script created and tested
- ✅ API connection verified
- ✅ 31 critical variables ready
- ⚠️ API bulk updates not supported (405 error)
- ✅ Dashboard import method validated

**Recommended Next Steps:**
1. Use Render Dashboard to import 31 critical variables
2. Trigger deployments for all services
3. Verify services start successfully
4. Test health endpoints
5. Add optional variables later as needed

**Estimated Time:**
- Dashboard configuration: 15-20 minutes
- Service deployment: 10-15 minutes
- Testing/verification: 5-10 minutes
- **Total: 30-45 minutes**

---

**Last Updated:** 2025-11-08
**Script Location:** `scripts/configure_render_env.py`
**Blueprint ID:** exs-d473mme3jp1c73booqig
