# Environment Variables Quick Reference

## Complete Variable List for All Services

---

## 🎯 Render Backend Variables

### Required Variables (18 total)

| Variable | Example Value | Where to Get | Required |
|----------|---------------|--------------|----------|
| **SUPABASE_URL** | `https://xyz.supabase.co` | Supabase → Settings → API | ✅ |
| **SUPABASE_ANON_KEY** | `eyJhbGc...` | Supabase → Settings → API | ✅ |
| **SUPABASE_SERVICE_ROLE_KEY** | `eyJhbGc...` | Supabase → Settings → API | ✅ |
| **DATABASE_URL** | `postgresql://postgres:pass@host:5432/db` | Supabase → Settings → Database | ✅ |
| **CLERK_SECRET_KEY** | `sk_test_xxx` or `sk_live_xxx` | Clerk → API Keys | ✅ |
| **CLERK_PUBLISHABLE_KEY** | `pk_test_xxx` or `pk_live_xxx` | Clerk → API Keys | ✅ |
| **JWT_SECRET_KEY** | `a1b2c3...` (64 chars) | Generate: `openssl rand -hex 32` | ✅ |
| **JWT_ALGORITHM** | `HS256` | Manual entry | ✅ |
| **JWT_ACCESS_TOKEN_EXPIRE_MINUTES** | `60` | Manual entry | ✅ |
| **PUSHER_APP_ID** | `1234567` | Pusher → App Keys | ✅ |
| **PUSHER_KEY** | `a1b2c3d4e5f6` | Pusher → App Keys | ✅ |
| **PUSHER_SECRET** | `k1l2m3n4o5p6` | Pusher → App Keys | ✅ |
| **PUSHER_CLUSTER** | `us2` | Pusher → App Keys | ✅ |
| **CORS_ORIGINS** | `https://domain.vercel.app,https://domain-*.vercel.app` | Manual entry (your Vercel domain) | ✅ |
| **ENVIRONMENT** | `production` | Manual entry | ✅ |
| **DEBUG** | `false` | Manual entry | ✅ |
| **PYTHONPATH** | `/opt/render/project/src` | Manual entry | ✅ |
| **PYTHON_VERSION** | `3.12.0` | Manual entry | ✅ |

### Optional Variables (6 total)

| Variable | Example Value | Where to Get | Required |
|----------|---------------|--------------|----------|
| **OPENAI_API_KEY** | `sk-proj-xxx...` | OpenAI → API Keys | ⭕ Optional |
| **ANTHROPIC_API_KEY** | `sk-ant-xxx...` | Anthropic → API Keys | ⭕ Optional |
| **SENDGRID_API_KEY** | `SG.xxx...` | SendGrid → Settings → API Keys | ⭕ Optional |
| **SENDGRID_FROM_EMAIL** | `noreply@domain.com` | Manual entry | ⭕ Optional |
| **SENTRY_DSN** | `https://xxx@o123.ingest.sentry.io/456` | Sentry → Project Settings → Client Keys | ⭕ Optional |
| **NODE_ENV** | `production` | Manual entry | ⭕ Optional |

---

## 🌐 Vercel Frontend Variables

### Required Variables (12 total)

| Variable | Example Value | Where to Get | Required |
|----------|---------------|--------------|----------|
| **VITE_API_BASE_URL** | `https://toolboxai-backend.onrender.com` | Your Render backend URL | ✅ |
| **VITE_WS_URL** | `wss://toolboxai-backend.onrender.com` | Your Render backend URL (with wss://) | ✅ |
| **VITE_CLERK_PUBLISHABLE_KEY** | `pk_test_xxx` or `pk_live_xxx` | Clerk → API Keys | ✅ |
| **NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY** | `pk_test_xxx` or `pk_live_xxx` | Clerk → API Keys (same as above) | ✅ |
| **VITE_ENABLE_CLERK_AUTH** | `true` | Manual entry | ✅ |
| **VITE_SUPABASE_URL** | `https://xyz.supabase.co` | Supabase → Settings → API | ✅ |
| **VITE_SUPABASE_ANON_KEY** | `eyJhbGc...` | Supabase → Settings → API | ✅ |
| **NEXT_PUBLIC_SUPABASE_URL** | `https://xyz.supabase.co` | Supabase → Settings → API (same as above) | ✅ |
| **NEXT_PUBLIC_SUPABASE_ANON_KEY** | `eyJhbGc...` | Supabase → Settings → API (same as above) | ✅ |
| **VITE_PUSHER_KEY** | `a1b2c3d4e5f6` | Pusher → App Keys | ✅ |
| **VITE_PUSHER_CLUSTER** | `us2` | Pusher → App Keys | ✅ |
| **VITE_PUSHER_AUTH_ENDPOINT** | `/pusher/auth` | Manual entry | ✅ |
| **VITE_ENABLE_PUSHER** | `true` | Manual entry | ✅ |

### Optional Variables (3 total)

| Variable | Example Value | Where to Get | Required |
|----------|---------------|--------------|----------|
| **VITE_ENABLE_ANALYTICS** | `true` | Manual entry | ⭕ Optional |
| **VITE_SENTRY_DSN** | `https://xxx@o123.ingest.sentry.io/789` | Sentry → Project Settings (frontend project) | ⭕ Optional |
| **VITE_ENABLE_DEBUG_MODE** | `false` | Manual entry | ⭕ Optional |

---

## 📋 Copy-Paste Templates

### For Render Backend

Copy this template and replace placeholder values:

```bash
# Database - Supabase
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR-ANON-KEY-HERE
SUPABASE_SERVICE_ROLE_KEY=YOUR-SERVICE-ROLE-KEY-HERE
DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.YOUR-PROJECT.supabase.co:5432/postgres

# Authentication - Clerk
CLERK_SECRET_KEY=sk_live_YOUR-SECRET-KEY-HERE
CLERK_PUBLISHABLE_KEY=pk_live_YOUR-PUBLISHABLE-KEY-HERE

# JWT Security
JWT_SECRET_KEY=GENERATE-WITH-OPENSSL-RAND-HEX-32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Real-time - Pusher
PUSHER_APP_ID=YOUR-APP-ID
PUSHER_KEY=YOUR-PUSHER-KEY
PUSHER_SECRET=YOUR-PUSHER-SECRET
PUSHER_CLUSTER=us2

# CORS
CORS_ORIGINS=https://toolbox-production-final.vercel.app,https://toolbox-production-final-*.vercel.app

# System
ENVIRONMENT=production
DEBUG=false
PYTHONPATH=/opt/render/project/src
PYTHON_VERSION=3.12.0

# Optional - AI Services
# OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE
# ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE

# Optional - Email
# SENDGRID_API_KEY=SG.YOUR-KEY-HERE
# SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# Optional - Monitoring
# SENTRY_DSN=https://YOUR-DSN@sentry.io/YOUR-PROJECT-ID
```

### For Vercel Frontend

Copy this template and replace placeholder values:

```bash
# Backend API
VITE_API_BASE_URL=https://toolboxai-backend.onrender.com
VITE_WS_URL=wss://toolboxai-backend.onrender.com

# Authentication - Clerk
VITE_CLERK_PUBLISHABLE_KEY=pk_live_YOUR-PUBLISHABLE-KEY-HERE
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_YOUR-PUBLISHABLE-KEY-HERE
VITE_ENABLE_CLERK_AUTH=true

# Database - Supabase
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR-ANON-KEY-HERE
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR-ANON-KEY-HERE

# Real-time - Pusher
VITE_PUSHER_KEY=YOUR-PUSHER-KEY
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth
VITE_ENABLE_PUSHER=true

# Optional - Analytics
# VITE_ENABLE_ANALYTICS=true
# VITE_SENTRY_DSN=https://YOUR-DSN@sentry.io/YOUR-FRONTEND-PROJECT-ID
```

---

## 🔍 Variable Validation

### How to Test Each Service

#### Supabase Database
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Should return: 1 row
```

#### Clerk Authentication
```bash
# Test with curl
curl -H "Authorization: Bearer $CLERK_SECRET_KEY" \
  https://api.clerk.com/v1/users

# Should return: JSON with users list
```

#### Pusher Channels
```bash
# Test with curl (requires signature - use Pusher dashboard for testing)
# Or check backend logs when connecting
```

#### JWT Secret
```bash
# Verify it's at least 32 characters
echo $JWT_SECRET_KEY | wc -c
# Should be: 64 or more
```

---

## ⚠️ Security Checklist

### Never Commit These to Git
- ❌ `SUPABASE_SERVICE_ROLE_KEY` - Full database access
- ❌ `CLERK_SECRET_KEY` - Can manipulate users
- ❌ `JWT_SECRET_KEY` - Can forge authentication tokens
- ❌ `PUSHER_SECRET` - Can trigger unauthorized events
- ❌ `DATABASE_URL` with password
- ❌ `OPENAI_API_KEY` - Costs money
- ❌ `SENDGRID_API_KEY` - Can send emails

### Safe to Commit (in .env.example)
- ✅ `VITE_CLERK_PUBLISHABLE_KEY` (public key)
- ✅ `VITE_SUPABASE_URL` (public URL)
- ✅ `VITE_SUPABASE_ANON_KEY` (read-only public key)
- ✅ `VITE_PUSHER_KEY` (public key)
- ✅ All `VITE_ENABLE_*` flags
- ✅ All `*_CLUSTER` values

---

## 🔄 Variable Dependencies

### Required Order of Setup

1. **Generate JWT Secret** (no dependencies)
   ```bash
   openssl rand -hex 32
   ```

2. **Set up Supabase** (no dependencies)
   - Get all 4 Supabase variables

3. **Set up Clerk** (no dependencies)
   - Get both Clerk keys

4. **Set up Pusher** (no dependencies)
   - Get all 4 Pusher variables

5. **Deploy Backend to Render** (needs all above)
   - Add all variables from steps 1-4

6. **Deploy Frontend to Vercel** (needs backend URL from step 5)
   - Use backend URL from Render
   - Add Clerk, Supabase, Pusher public keys

---

## 🚨 Common Mistakes

### ❌ Wrong Format Examples

| Variable | Wrong | Correct |
|----------|-------|---------|
| CORS_ORIGINS | `"https://domain.com"` | `https://domain.com` (no quotes in Render UI) |
| DATABASE_URL | `postgres://...` | `postgresql://...` (postgresql not postgres) |
| VITE_API_BASE_URL | `http://backend.com/` | `https://backend.com` (https, no trailing slash) |
| VITE_WS_URL | `https://backend.com` | `wss://backend.com` (wss not https) |
| JWT_SECRET_KEY | `"my_secret"` | (64+ char hex from openssl) |
| ENVIRONMENT | `Production` | `production` (lowercase) |
| DEBUG | `False` | `false` (lowercase) |

---

## 📊 Total Variable Count

- **Render Backend:** 18 required + 6 optional = **24 variables**
- **Vercel Frontend:** 13 required + 3 optional = **16 variables**
- **Total:** 31 required + 9 optional = **40 variables**

---

## 🔗 Quick Links to Get Credentials

| Service | Dashboard URL | What to Get |
|---------|--------------|-------------|
| **Supabase** | https://app.supabase.com/ | URL, Anon Key, Service Role Key, Database URL |
| **Clerk** | https://dashboard.clerk.com/ | Secret Key, Publishable Key |
| **Pusher** | https://dashboard.pusher.com/ | App ID, Key, Secret, Cluster |
| **OpenAI** | https://platform.openai.com/api-keys | API Key |
| **Anthropic** | https://console.anthropic.com/ | API Key |
| **SendGrid** | https://app.sendgrid.com/settings/api_keys | API Key |
| **Sentry** | https://sentry.io/settings/ | DSN |

---

## ✅ Ready to Deploy?

### Quick Verification

Before deploying, verify you have:

**Render Backend:**
- [ ] 4 Supabase variables
- [ ] 2 Clerk variables
- [ ] 3 JWT variables
- [ ] 4 Pusher variables
- [ ] 1 CORS variable
- [ ] 4 System variables

**Vercel Frontend:**
- [ ] 2 Backend URL variables
- [ ] 2 Clerk variables (publishable only)
- [ ] 4 Supabase variables (URL and anon key × 2)
- [ ] 4 Pusher variables

**Total: 31 Required Variables**

---

**Last Updated:** October 21, 2025
**Complete Reference:** All environment variables for ToolboxAI deployment
