# Environment Configuration Guide

**Date:** November 10, 2025
**Purpose:** Complete guide for configuring environment variables across all deployment platforms
**Status:** Reference Guide
**Priority:** P0 CRITICAL

---

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Render Backend Configuration](#render-backend-configuration)
3. [Vercel Frontend Configuration](#vercel-frontend-configuration)
4. [GitHub Secrets Configuration](#github-secrets-configuration)
5. [Local Development Configuration](#local-development-configuration)
6. [Validation](#validation)

---

## Configuration Overview

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Actions (CI/CD)                      │
│  Secrets: RENDER_API_KEY, VERCEL_TOKEN, GITHUB_TOKEN       │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        v                 v
┌───────────────┐   ┌─────────────────┐
│ Render        │   │ Vercel          │
│ (Backend API) │   │ (Frontend SPA)  │
│               │   │                 │
│ Environment:  │   │ Environment:    │
│ - P0 Secrets  │   │ - VITE_ vars    │
│ - Database    │   │ - Public keys   │
│ - API Keys    │   │ - API URL       │
└───────┬───────┘   └────────┬────────┘
        │                    │
        v                    v
┌─────────────────┐   ┌──────────────┐
│ Supabase        │   │ Pusher       │
│ PostgreSQL      │   │ Real-time    │
│ Storage         │   │ Channels     │
└─────────────────┘   └──────────────┘
```

### Priority Levels

| Priority | Description | Impact if Missing |
|----------|-------------|-------------------|
| **P0** | Critical - Required for startup | Service fails to start |
| **P1** | High - Core functionality | Features degraded or disabled |
| **P2** | Medium - Optional features | Optional features unavailable |
| **P3** | Low - Development/debugging | Development experience affected |

---

## Render Backend Configuration

### Access Render Dashboard

1. Go to https://dashboard.render.com
2. Navigate to **toolboxai-backend** service
3. Click **Environment** tab
4. Use **Environment Groups** for secrets (recommended)

### Environment Variable Groups

Render uses **Environment Groups** to manage shared secrets across services.

#### Create `toolboxai-secrets` Group

1. Render Dashboard → **Environment Groups**
2. Click **New Environment Group**
3. Name: `toolboxai-secrets`
4. Add variables below
5. Link to services: `toolboxai-backend`, `toolboxai-mcp`, `toolboxai-agent-coordinator`

### P0 Critical Variables (MUST Configure)

These variables are **required** for the backend to start successfully:

```bash
# ============================================
# DATABASE & CACHE (P0)
# ============================================

# Supabase Database Connection
# Get from: https://supabase.com/dashboard → Your Project → Settings → Database
# Connection string format (use Pooler, port 6543):
SUPABASE_DATABASE_URL=postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require

# Also set as DATABASE_URL (main database URL)
DATABASE_URL=${SUPABASE_DATABASE_URL}

# Note: REDIS_URL is auto-populated by Render from Redis service
# No manual configuration needed

# ============================================
# SUPABASE INTEGRATION (P0)
# ============================================

# Supabase API Configuration
# Get from: https://supabase.com/dashboard → Your Project → Settings → API
SUPABASE_URL=https://[PROJECT-ID].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # JWT token (starts with eyJ)
SUPABASE_ANON_KEY=eyJhbGc...  # Public anon key (for client-side if needed)

# ============================================
# SECURITY & AUTHENTICATION (P0)
# ============================================

# JWT Token Secrets (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=<64-char-hex-string>
JWT_REFRESH_SECRET_KEY=<64-char-hex-string>
JWT_ALGORITHM=HS256

# Application Security Keys (generate with: openssl rand -hex 32)
SECRET_KEY=<64-char-hex-string>
ENCRYPTION_KEY=<32-char-hex-string>
SESSION_SECRET_KEY=<64-char-hex-string>
CSRF_SECRET_KEY=<64-char-hex-string>
RATE_LIMIT_SECRET=<32-char-hex-string>

# ============================================
# AI SERVICES (P0 if AI features enabled)
# ============================================

# OpenAI API Key (required for AI features)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-...

# ============================================
# CORS & SECURITY (P0)
# ============================================

# Allowed frontend origins (comma-separated, no spaces)
ALLOWED_ORIGINS=https://toolboxai-dashboard.vercel.app,https://toolboxai-solutions-4sebumacd-grayghostdevs-projects.vercel.app,https://*.vercel.app

# Trusted backend hosts
TRUSTED_HOSTS=toolboxai-backend-8j12.onrender.com,localhost,127.0.0.1

# Security flags
HTTPS_ONLY=true
SECURE_COOKIES=true
SECURITY_HEADERS_ENABLED=true
```

### P1 High Priority Variables (Recommended)

These enable core features but are not critical for startup:

```bash
# ============================================
# CLERK AUTHENTICATION (P1 if using Clerk)
# ============================================

# Get from: https://dashboard.clerk.com → Your App → API Keys
CLERK_SECRET_KEY=sk_live_...
CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_WEBHOOK_SIGNING_SECRET=whsec_...
CLERK_JWKS_URL=https://[your-domain].clerk.accounts.dev/.well-known/jwks.json

# ============================================
# PUSHER CHANNELS (P1 for real-time features)
# ============================================

# Get from: https://dashboard.pusher.com → Your App → App Keys
PUSHER_APP_ID=1234567
PUSHER_KEY=abcdef123456
PUSHER_SECRET=xyz789secret
PUSHER_CLUSTER=us2
PUSHER_SSL=true

# ============================================
# LANGCHAIN/LANGSMITH (P1 for AI observability)
# ============================================

# Get from: https://smith.langchain.com → Settings → API Keys
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=ToolboxAI-Solutions
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# ============================================
# SENTRY (P1 for error tracking)
# ============================================

# Get from: https://sentry.io → Project → Settings → Client Keys
SENTRY_DSN=https://[KEY]@[ORG].ingest.sentry.io/[PROJECT]
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=${RENDER_GIT_COMMIT}

# Backend-specific DSN
SENTRY_DSN_BACKEND=${SENTRY_DSN}
```

### P2 Optional Variables

```bash
# Anthropic Claude API (alternative AI provider)
ANTHROPIC_API_KEY=sk-ant-...

# Google AI API
GOOGLE_AI_API_KEY=...

# Replicate API (for additional models)
REPLICATE_API_TOKEN=r8_...

# GitHub Token (for integrations)
GITHUB_TOKEN=ghp_...

# Monitoring integrations
DATADOG_API_KEY=...
NEW_RELIC_LICENSE_KEY=...
```

### Application Settings (Non-Secret)

These can be set directly in `render.production.yaml`:

```bash
# Application environment
ENVIRONMENT=production
LOG_LEVEL=info

# Python version
PYTHON_VERSION=3.12.0

# Database connection pool settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Rate limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
```

### How to Configure

#### Option 1: Environment Groups (Recommended)

1. Render Dashboard → **Environment Groups**
2. Select `toolboxai-secrets` (or create if missing)
3. Click **Add Variable**
4. Enter key and value
5. Click **Save**
6. Link group to service if not already linked

**Advantages:**
- Share secrets across multiple services
- Easier to manage
- Better organization

#### Option 2: Direct Service Configuration

1. Render Dashboard → **toolboxai-backend** → Environment
2. Click **Add Environment Variable**
3. Enter key and value
4. Click **Save Changes**
5. Service will auto-deploy with new variables

**Advantages:**
- Service-specific configuration
- Override group variables

---

## Vercel Frontend Configuration

### Access Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Select **toolboxai-solutions** project
3. Go to **Settings → Environment Variables**
4. Select **Production** environment

### Required Variables

```bash
# ============================================
# BACKEND API CONFIGURATION (P0)
# ============================================

# Backend API base URL
VITE_API_URL=https://toolboxai-backend-8j12.onrender.com
VITE_API_BASE_URL=https://toolboxai-backend-8j12.onrender.com

# Environment
VITE_ENVIRONMENT=production
VITE_NODE_ENV=production

# ============================================
# SUPABASE (P0)
# ============================================

# Get from: https://supabase.com/dashboard → Your Project → Settings → API
VITE_SUPABASE_URL=https://[PROJECT-ID].supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...  # Public anon key

# ============================================
# AUTHENTICATION (P1 if using Clerk)
# ============================================

# Get from: https://dashboard.clerk.com → Your App → API Keys
VITE_CLERK_PUBLISHABLE_KEY=pk_live_...
VITE_CLERK_SIGN_IN_URL=/sign-in
VITE_CLERK_SIGN_UP_URL=/sign-up
VITE_CLERK_AFTER_SIGN_IN_URL=/dashboard
VITE_CLERK_AFTER_SIGN_UP_URL=/dashboard
VITE_ENABLE_CLERK_AUTH=true

# ============================================
# REAL-TIME (P1 for Pusher)
# ============================================

# Get from: https://dashboard.pusher.com → Your App → App Keys
VITE_PUSHER_KEY=abcdef123456  # Same as backend PUSHER_KEY
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/api/v1/pusher/auth
VITE_ENABLE_PUSHER=true

# ============================================
# MONITORING (P2)
# ============================================

# Sentry for frontend error tracking
VITE_SENTRY_DSN=https://[KEY]@[ORG].ingest.sentry.io/[PROJECT]

# Google Analytics
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# ============================================
# FEATURE FLAGS (P2)
# ============================================

VITE_ENABLE_ROBLOX_INTEGRATION=true
VITE_ENABLE_GAMIFICATION=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_AI_CHAT=true

# ============================================
# COMPLIANCE (P2)
# ============================================

VITE_COPPA_COMPLIANCE=true
VITE_FERPA_COMPLIANCE=true
VITE_GDPR_COMPLIANCE=true
```

### How to Configure

1. Vercel Dashboard → **toolboxai-solutions** → Settings → Environment Variables
2. Click **Add**
3. Enter:
   - **Key:** Variable name (e.g., `VITE_API_URL`)
   - **Value:** Variable value
   - **Environment:** Select **Production** (or Preview/Development as needed)
4. Click **Save**
5. **Important:** Redeploy to apply changes
   - Go to **Deployments**
   - Click **...** → **Redeploy**

### Environment Scopes

| Scope | When Used | Example |
|-------|-----------|---------|
| **Production** | Production deployments (main branch) | `VITE_API_URL=https://toolboxai-backend-8j12.onrender.com` |
| **Preview** | Preview deployments (PRs) | `VITE_API_URL=https://toolboxai-backend-staging.onrender.com` |
| **Development** | Local development (`vercel dev`) | `VITE_API_URL=http://localhost:8009` |

---

## GitHub Secrets Configuration

### Access GitHub Secrets

1. Go to https://github.com/GrayGhostDev/ToolBoxAI-Solutions
2. Go to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**

### Required Secrets

```bash
# ============================================
# RENDER DEPLOYMENT (P0)
# ============================================

# Render API Key for deployment automation
# Get from: https://dashboard.render.com → Account Settings → API Keys
RENDER_API_KEY=rnd_...

# Render Service ID for backend service
# Get from: Render Dashboard → toolboxai-backend → Settings (check URL)
RENDER_SERVICE_ID=srv-...

# Backend health check URL (optional, has default)
BACKEND_HEALTH_URL=https://toolboxai-backend-8j12.onrender.com/health

# ============================================
# VERCEL DEPLOYMENT (P0)
# ============================================

# Vercel Token for deployment automation
# Get from: https://vercel.com/account/tokens
VERCEL_TOKEN=...

# Vercel Organization ID
# Get from: Vercel → Settings → General (or run: vercel whoami)
VERCEL_ORG_ID=...

# Vercel Project ID
# Get from: Vercel → Project Settings → General
VERCEL_PROJECT_ID=...

# Vercel Build Hook URL (alternative to CLI deploy)
# Get from: Vercel → Settings → Git → Deploy Hooks
VERCEL_BUILD_HOOK_URL=https://api.vercel.com/v1/integrations/deploy/...

# ============================================
# GITHUB INTEGRATION (P1)
# ============================================

# GitHub Personal Access Token (for repo operations)
# Get from: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_...

# ============================================
# BACKEND/FRONTEND URLS (P2 for testing)
# ============================================

# Used in smoke tests after deployment
BACKEND_URL=https://toolboxai-backend-8j12.onrender.com
FRONTEND_URL=https://toolboxai-dashboard.vercel.app
```

### How to Configure

1. GitHub → Repository → Settings → Secrets and variables → Actions
2. Click **New repository secret**
3. Enter:
   - **Name:** Secret name (e.g., `RENDER_API_KEY`)
   - **Secret:** Secret value
4. Click **Add secret**
5. Repeat for all secrets

**Note:** GitHub Secrets are encrypted and not visible after creation.

---

## Local Development Configuration

### Setup Local Environment

1. **Copy example file:**
   ```bash
   cd /path/to/ToolBoxAI-Solutions
   cp .env.example .env
   ```

2. **Generate secrets:**
   ```bash
   ./scripts/generate-secrets.sh > .env.secrets
   ```

3. **Edit `.env` file:**
   ```bash
   # Open in your editor
   code .env  # VS Code
   # or
   nano .env  # Terminal editor
   ```

4. **Configure P0 variables:**

```bash
# ============================================
# LOCAL DEVELOPMENT CONFIGURATION
# ============================================

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Backend
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8009

# Frontend
VITE_API_BASE_URL=http://127.0.0.1:8009

# Database (use Supabase or local PostgreSQL)
# Option 1: Supabase (recommended for development)
SUPABASE_URL=https://[PROJECT-ID].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:6543/postgres

# Option 2: Local PostgreSQL
# DATABASE_URL=postgresql://dbuser:password@localhost:5432/toolboxai_dev

# Redis (local or Render)
# Option 1: Local Redis
REDIS_URL=redis://localhost:6379/0

# Option 2: Render Redis (use Render's REDIS_URL from dashboard)
# REDIS_URL=redis://...(from Render)

# Copy secrets from .env.secrets
JWT_SECRET_KEY=<from .env.secrets>
SECRET_KEY=<from .env.secrets>
ENCRYPTION_KEY=<from .env.secrets>

# API Keys (use test keys or personal keys)
OPENAI_API_KEY=sk-proj-...  # Get from OpenAI dashboard
```

5. **Verify configuration:**
   ```bash
   python scripts/validate-env.py
   ```

### Docker Compose Development

For local development with Docker:

```bash
# Use docker-compose.dev.yml
cp infrastructure/docker/compose/.env.example infrastructure/docker/compose/.env

# Edit infrastructure/docker/compose/.env
# Configure same variables as above

# Start services
docker-compose -f infrastructure/docker/compose/docker-compose.dev.yml up -d
```

---

## Validation

### Validate Environment Configuration

#### Render Backend Validation

```bash
# Check if all P0 variables are configured in Render
# (Manual check in Render Dashboard → Environment)

# Test backend is accessible
curl -I https://toolboxai-backend-8j12.onrender.com/health
# Expected: HTTP/2 200

# Run health check script
./scripts/check-backend-health.sh
```

#### Vercel Frontend Validation

```bash
# Check Vercel environment variables
# (Manual check in Vercel Dashboard → Settings → Environment Variables)

# Test frontend is accessible
curl -I https://toolboxai-dashboard.vercel.app
# Expected: HTTP/2 200
```

#### Local Development Validation

```bash
# Validate .env file
python scripts/validate-env.py

# Expected output:
# [P0] Critical Variables: X/X passed
# [P1] High Priority Variables: X/X passed
# ✓ Environment validation passed
```

### Automated Validation Script

Run this to check all configurations:

```bash
#!/bin/bash
# Comprehensive environment validation

echo "Validating ToolBoxAI environment configuration..."
echo ""

# 1. Validate local .env
echo "1. Validating local .env..."
python scripts/validate-env.py
echo ""

# 2. Check backend health
echo "2. Checking backend health..."
./scripts/check-backend-health.sh
echo ""

# 3. Test frontend
echo "3. Testing frontend..."
curl -I https://toolboxai-dashboard.vercel.app
echo ""

# 4. Test CORS
echo "4. Testing CORS..."
curl -H "Origin: https://toolboxai-dashboard.vercel.app" \
  -I https://toolboxai-backend-8j12.onrender.com/health | grep -i "access-control"
echo ""

echo "Validation complete!"
```

---

## Summary Checklist

### Before Deployment

- [ ] **Generate Secrets**
  ```bash
  ./scripts/generate-secrets.sh > .env.secrets
  ```

- [ ] **Configure Render Backend**
  - [ ] Create `toolboxai-secrets` environment group
  - [ ] Add all P0 variables from `.env.secrets`
  - [ ] Configure Supabase connection (URL, keys, DATABASE_URL)
  - [ ] Set ALLOWED_ORIGINS for CORS
  - [ ] Verify REDIS_URL is auto-populated

- [ ] **Configure Vercel Frontend**
  - [ ] Set `VITE_API_URL` to backend URL
  - [ ] Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
  - [ ] Set `VITE_PUSHER_KEY` and `VITE_PUSHER_CLUSTER`
  - [ ] Set `VITE_CLERK_PUBLISHABLE_KEY` (if using Clerk)

- [ ] **Configure GitHub Secrets**
  - [ ] Add `RENDER_API_KEY` and `RENDER_SERVICE_ID`
  - [ ] Add `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
  - [ ] Add `GITHUB_TOKEN` (if using GitHub integrations)

- [ ] **Validate Configuration**
  - [ ] Run `./scripts/check-backend-health.sh`
  - [ ] Run `python scripts/validate-env.py --check-render`
  - [ ] Test frontend → backend connectivity
  - [ ] Verify CORS headers
  - [ ] Check error tracking (Sentry) works

---

**Report Generated:** November 10, 2025
**Next Review:** After environment configuration
**Status:** Reference Guide - Use for configuration
