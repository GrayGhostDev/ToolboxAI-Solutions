# Environment Variable Audit - November 10, 2025

**Project:** ToolBoxAI-Solutions Platform Integration
**Audit Date:** 2025-11-10
**Status:** Phase 1 Discovery Complete

---

## Executive Summary

This audit identifies all environment variables required for the ToolBoxAI-Solutions platform across all deployment targets (Render backend, Vercel frontend, Supabase database, Docker local, GitHub Actions).

**Total Variables Identified:** 150+
**Critical Missing:** TBD (Phase 2)
**Deployment Targets:** 5

---

## Render Backend Environment Variables

### Database & Cache (Critical - P0)
- [ ] `DATABASE_URL` - PostgreSQL connection (should use SUPABASE_DATABASE_URL)
- [ ] `SUPABASE_URL` - Supabase project URL
- [ ] `SUPABASE_SERVICE_ROLE_KEY` - Supabase admin key
- [ ] `SUPABASE_DATABASE_URL` - Supabase PostgreSQL with pooler (port 6543)
- [ ] `REDIS_URL` - Redis cache connection (auto-configured from Render Redis service)

### Security & Authentication (Critical - P0)
- [ ] `JWT_SECRET_KEY` - JWT signing key (generate with openssl rand -hex 32)
- [ ] `JWT_REFRESH_SECRET_KEY` - Refresh token signing key
- [ ] `SECRET_KEY` - Application secret key
- [ ] `ENCRYPTION_KEY` - Data encryption key
- [ ] `SESSION_SECRET_KEY` - Session encryption
- [ ] `CSRF_SECRET_KEY` - CSRF protection
- [ ] `RATE_LIMIT_SECRET` - Rate limiting

### Clerk Authentication (High - P1)
- [ ] `CLERK_SECRET_KEY` - Backend authentication
- [ ] `CLERK_PUBLISHABLE_KEY` - Public key for frontend
- [ ] `CLERK_WEBHOOK_SIGNING_SECRET` - Webhook validation
- [ ] `CLERK_JWKS_URL` - JWT validation endpoint

### AI/ML Services (Critical - P0)
- [ ] `OPENAI_API_KEY` - OpenAI GPT-4.1 API
- [ ] `ANTHROPIC_API_KEY` - Claude API (optional)
- [ ] `GOOGLE_AI_API_KEY` - Google AI (optional)
- [ ] `REPLICATE_API_TOKEN` - Additional models (optional)

### LangChain & Observability (High - P1)
- [ ] `LANGCHAIN_API_KEY` - LangChain API access
- [ ] `LANGCHAIN_PROJECT` - Project name (default: "ToolboxAI-Solutions")
- [ ] `LANGCHAIN_TRACING_V2` - Enable tracing (default: "true")
- [ ] `LANGCHAIN_ENDPOINT` - API endpoint (default: https://api.smith.langchain.com)
- [ ] `LANGCACHE_API_KEY` - Semantic caching (optional)
- [ ] `LANGCACHE_CACHE_ID` - Cache identifier (optional)

### Supabase Storage (High - P1)
- [ ] `STORAGE_BACKEND` - Storage type (default: "supabase")
- [ ] `SUPABASE_STORAGE_BUCKET` - Bucket name (default: "toolboxai-uploads")
- [ ] `SUPABASE_S3_ENDPOINT` - S3-compatible endpoint
- [ ] `SUPABASE_S3_REGION` - Region (e.g., "us-east-1")
- [ ] `SUPABASE_S3_ACCESS_KEY_ID` - S3 access key
- [ ] `SUPABASE_S3_SECRET_ACCESS_KEY` - S3 secret key
- [ ] `SUPABASE_SSL_CERT_B64` - SSL certificate (base64 encoded, optional)

### Real-Time Services (High - P1)
- [ ] `PUSHER_APP_ID` - Pusher application ID
- [ ] `PUSHER_KEY` - Pusher public key
- [ ] `PUSHER_SECRET` - Pusher secret key
- [ ] `PUSHER_CLUSTER` - Geographic cluster (default: "us2")

### Monitoring & Logging (Medium - P2)
- [ ] `SENTRY_DSN` - Sentry error tracking
- [ ] `SENTRY_ENVIRONMENT` - Environment name (default: "production")
- [ ] `SENTRY_RELEASE` - Release version (auto: ${RENDER_GIT_COMMIT})
- [ ] `DATADOG_API_KEY` - Datadog APM (optional)
- [ ] `NEW_RELIC_LICENSE_KEY` - New Relic (optional)

### Application Configuration (Medium - P2)
- [ ] `ENVIRONMENT` - Environment name (default: "production")
- [ ] `LOG_LEVEL` - Logging level (default: "info")
- [ ] `ALLOWED_ORIGINS` - CORS origins (comma-separated)
- [ ] `TRUSTED_HOSTS` - Trusted hostnames (comma-separated)
- [ ] `PYTHON_VERSION` - Python version (default: "3.12.0")

### Performance Tuning (Medium - P2)
- [ ] `DB_POOL_SIZE` - Database connection pool size (default: 5 for Starter)
- [ ] `DB_MAX_OVERFLOW` - Max overflow connections (default: 5)
- [ ] `DB_POOL_TIMEOUT` - Connection timeout seconds (default: 30)
- [ ] `DB_POOL_RECYCLE` - Connection recycle time (default: 3600)
- [ ] `RATE_LIMIT_REQUESTS` - Rate limit per window (default: 1000)
- [ ] `RATE_LIMIT_WINDOW` - Rate limit window seconds (default: 60)

### Security Headers (Medium - P2)
- [ ] `SECURITY_HEADERS_ENABLED` - Enable security headers (default: "true")
- [ ] `HTTPS_ONLY` - Force HTTPS (default: "true")
- [ ] `SECURE_COOKIES` - Secure cookie flag (default: "true")

### External Integrations (Low - P3)
- [ ] `GITHUB_TOKEN` - GitHub API access
- [ ] `STRIPE_PUBLISHABLE_KEY` - Payment processing
- [ ] `STRIPE_SECRET_KEY` - Payment processing
- [ ] `STRIPE_WEBHOOK_SECRET` - Payment webhooks
- [ ] `SENDGRID_API_KEY` - Email sending
- [ ] `TWILIO_ACCOUNT_SID` - SMS/phone
- [ ] `TWILIO_AUTH_TOKEN` - SMS/phone

### Celery Background Jobs (High - P1)
- [ ] `CELERY_BROKER_URL` - Celery broker (auto-configured from Redis)
- [ ] `CELERY_RESULT_BACKEND` - Result storage (auto-configured from Redis)
- [ ] `CELERY_WORKER_CONCURRENCY` - Worker threads (default: 2 for Starter)
- [ ] `CELERY_WORKER_POOL` - Worker pool type (default: "prefork")
- [ ] `CELERY_TASK_TIME_LIMIT` - Hard timeout (default: 300)
- [ ] `CELERY_TASK_SOFT_TIME_LIMIT` - Soft timeout (default: 270)
- [ ] `CELERY_WORKER_MAX_TASKS_PER_CHILD` - Task recycling (default: 1000)
- [ ] `CELERY_BEAT_LOG_LEVEL` - Beat scheduler logging (default: "info")
- [ ] `CELERY_BEAT_MAX_LOOP_INTERVAL` - Beat loop interval (default: 60)
- [ ] `FLOWER_BASIC_AUTH` - Flower dashboard auth (format: "user:pass")

### Agent Coordinator (Medium - P2)
- [ ] `COORDINATOR_MAX_AGENTS` - Max concurrent agents (default: 25)
- [ ] `TASK_TIMEOUT` - Agent task timeout (default: 300)
- [ ] `MCP_SERVER_URL` - MCP server WebSocket URL (default: wss://toolboxai-mcp.onrender.com)
- [ ] `MCP_MAX_TOKENS` - Max tokens per request (default: 8192)
- [ ] `AGENT_DISCOVERY_ENABLED` - Enable agent discovery (default: "true")

---

## Vercel Frontend Environment Variables

### API Configuration (Critical - P0)
- [ ] `VITE_API_URL` - Backend API URL (https://toolboxai-backend-8j12.onrender.com)
- [ ] `VITE_API_BASE_URL` - Base API URL (same as VITE_API_URL)
- [ ] `VITE_ENVIRONMENT` - Environment name (default: "production")

### Supabase Frontend (High - P1)
- [ ] `VITE_SUPABASE_URL` - Supabase project URL
- [ ] `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key (public)
- [ ] `VITE_SUPABASE_S3_ENDPOINT` - Storage endpoint
- [ ] `VITE_SUPABASE_S3_REGION` - Storage region (default: "us-east-2")

### Clerk Authentication (High - P1)
- [ ] `VITE_CLERK_PUBLISHABLE_KEY` - Clerk public key
- [ ] `VITE_CLERK_FRONTEND_API_URL` - Clerk API endpoint
- [ ] `VITE_ENABLE_CLERK_AUTH` - Enable Clerk (default: "true")
- [ ] `VITE_CLERK_SIGN_IN_URL` - Sign-in page (default: "/sign-in")
- [ ] `VITE_CLERK_SIGN_UP_URL` - Sign-up page (default: "/sign-up")
- [ ] `VITE_CLERK_AFTER_SIGN_IN_URL` - Post-login redirect (default: "/dashboard")
- [ ] `VITE_CLERK_AFTER_SIGN_UP_URL` - Post-signup redirect (default: "/dashboard")

### Pusher Real-Time (High - P1)
- [ ] `VITE_PUSHER_KEY` - Pusher public key
- [ ] `VITE_PUSHER_CLUSTER` - Pusher cluster (default: "us2")
- [ ] `VITE_PUSHER_AUTH_ENDPOINT` - Auth endpoint (default: "/pusher/auth")
- [ ] `VITE_ENABLE_PUSHER` - Enable Pusher (default: "true")
- [ ] `VITE_ENABLE_WEBSOCKET` - Enable WebSockets (default: "true")

### Feature Flags (Medium - P2)
- [ ] `VITE_ENABLE_ROBLOX_INTEGRATION` - Roblox features (default: "true")
- [ ] `VITE_ENABLE_GAMIFICATION` - Gamification features (default: "true")
- [ ] `VITE_ENABLE_ANALYTICS` - Analytics tracking (default: "true")
- [ ] `VITE_ENABLE_2FA` - Two-factor auth (default: "true")
- [ ] `VITE_ENABLE_GITHUB_INTEGRATION` - GitHub integration (default: "true")
- [ ] `VITE_ENABLE_AI_CHAT` - AI chat features (default: "true")
- [ ] `VITE_BYPASS_AUTH` - Bypass auth for testing (default: "false")

### Monitoring (Medium - P2)
- [ ] `VITE_SENTRY_DSN` - Sentry frontend error tracking
- [ ] `VITE_GOOGLE_ANALYTICS_ID` - Google Analytics ID
- [ ] `VITE_STRIPE_PUBLISHABLE_KEY` - Stripe public key
- [ ] `VITE_HOTJAR_ID` - Hotjar tracking
- [ ] `VITE_MIXPANEL_TOKEN` - Mixpanel analytics
- [ ] `VITE_INTERCOM_APP_ID` - Intercom support chat
- [ ] `VITE_VERSION` - App version (default: "1.0.0")

### Roblox Integration (Medium - P2)
- [ ] `VITE_ROBLOX_API_URL` - Roblox API URL (default: https://api.roblox.com)
- [ ] `VITE_ROBLOX_UNIVERSE_ID` - Universe ID (8505376973)
- [ ] `VITE_ROBLOX_CLIENT_ID` - OAuth client ID (2214511122270781418)
- [ ] `VITE_ROBLOX_PLUGIN_PORT` - Plugin port (default: 64989)

### Compliance (Medium - P2)
- [ ] `VITE_COPPA_COMPLIANCE` - COPPA compliance mode (default: "true")
- [ ] `VITE_FERPA_COMPLIANCE` - FERPA compliance mode (default: "true")
- [ ] `VITE_GDPR_COMPLIANCE` - GDPR compliance mode (default: "true")

### Development (Low - P3)
- [ ] `VITE_DEBUG_MODE` - Debug mode (default: "false" in production)
- [ ] `VITE_MOCK_API` - Use mock API (default: "false")
- [ ] `VITE_E2E_TESTING` - E2E testing mode (default: "false")

### Build Configuration (Medium - P2)
- [ ] `ENABLE_EXPERIMENTAL_COREPACK` - Corepack support (default: "1")
- [ ] `NODE_VERSION` - Node.js version (default: "22")

---

## GitHub Actions Secrets

### Deployment Keys (Critical - P0)
- [ ] `RENDER_API_KEY` - Render deployment API key
- [ ] `VERCEL_TOKEN` - Vercel deployment token
- [ ] `VERCEL_ORG_ID` - Vercel organization ID
- [ ] `VERCEL_PROJECT_ID` - Vercel project ID

### Repository Access (High - P1)
- [ ] `GITHUB_TOKEN` - GitHub API access (auto-provided by Actions)
- [ ] `PAT_TOKEN` - Personal access token for private repos (if needed)

### Docker Registry (Medium - P2)
- [ ] `DOCKER_USERNAME` - Docker Hub username
- [ ] `DOCKER_PASSWORD` - Docker Hub password/token
- [ ] `DOCKER_REGISTRY` - Custom registry URL (optional)

### Supabase (High - P1)
- [ ] `SUPABASE_ACCESS_TOKEN` - Supabase CLI access
- [ ] `SUPABASE_PROJECT_ID` - Project identifier

### Monitoring & Alerts (Medium - P2)
- [ ] `SLACK_WEBHOOK_URL` - Deployment notifications
- [ ] `DISCORD_WEBHOOK_URL` - Deployment notifications
- [ ] `SENTRY_AUTH_TOKEN` - Release tracking

### Testing (Medium - P2)
- [ ] `CODECOV_TOKEN` - Code coverage reporting
- [ ] `SONAR_TOKEN` - SonarQube code quality

---

## Docker Local Development

### Core Services (Critical - P0)
- [ ] `DATABASE_URL` - PostgreSQL connection
- [ ] `POSTGRES_DB` - Database name (default: "toolboxai_dev")
- [ ] `POSTGRES_USER` - Database user (default: "dbuser")
- [ ] `POSTGRES_PASSWORD` - Database password
- [ ] `REDIS_URL` - Redis connection
- [ ] `REDIS_PASSWORD` - Redis password

### Application (High - P1)
- [ ] `FASTAPI_HOST` - Backend host (default: "0.0.0.0")
- [ ] `FASTAPI_PORT` - Backend port (default: 8009)
- [ ] `VITE_API_BASE_URL` - Frontend API URL (default: http://127.0.0.1:8009)
- [ ] `VITE_WS_URL` - WebSocket URL (default: ws://127.0.0.1:8009)

### Development Settings (Medium - P2)
- [ ] `DEBUG` - Debug mode (default: "true")
- [ ] `LOG_LEVEL` - Logging level (default: "DEBUG")
- [ ] `NODE_ENV` - Node environment (default: "development")
- [ ] `VITE_NODE_ENV` - Vite environment (default: "development")

### Docker Configuration (Low - P3)
- [ ] `DOCKER_BUILDKIT` - Enable BuildKit (default: "1")
- [ ] `COMPOSE_DOCKER_CLI_BUILD` - Use Docker CLI (default: "1")
- [ ] `DATA_DIR` - Data directory (default: "./data")

### Rojo Server (Medium - P2)
- [ ] `ROJO_SERVER_HOST` - Rojo host (default: "0.0.0.0")
- [ ] `ROJO_SERVER_PORT` - Rojo port (default: 34872)
- [ ] `ROJO_PROJECT_PATH` - Project config (default: "/app/default.project.json")
- [ ] `ROJO_LIVE_RELOAD` - Live reload (default: "true")
- [ ] `ROJO_DEV_MODE` - Dev mode (default: "false")
- [ ] `ROJO_LOG_LEVEL` - Logging (default: "info")

### HashiCorp Vault (Optional - P3)
- [ ] `VAULT_ENABLED` - Enable Vault (default: "false")
- [ ] `VAULT_ADDR` - Vault address (default: http://vault:8200)
- [ ] `VAULT_TOKEN` - Vault token
- [ ] `VAULT_NAMESPACE` - Vault namespace (Enterprise only)
- [ ] `VAULT_SKIP_VERIFY` - Skip TLS verify (dev only)
- [ ] `VAULT_DEV_ROOT_TOKEN` - Dev mode token (default: "devtoken")

### Monitoring Stack (Optional - P3)
- [ ] `GRAFANA_USER` - Grafana username (default: "admin")
- [ ] `GRAFANA_PASSWORD` - Grafana password
- [ ] `PROMETHEUS_RETENTION_TIME` - Retention period (default: "30d")
- [ ] `JAEGER_AGENT_HOST` - Jaeger host (default: "localhost")
- [ ] `JAEGER_SAMPLING_RATE` - Sampling rate (default: "0.01")

---

## Roblox Integration Variables

### OAuth & API (High - P1)
- [ ] `ROBLOX_UNIVERSE_ID` - Universe ID (8505376973)
- [ ] `ROBLOX_CLIENT_ID` - OAuth client ID (2214511122270781418)
- [ ] `ROBLOX_CLIENT_SECRET` - OAuth client secret
- [ ] `ROBLOX_API_KEY` - API key for Open Cloud
- [ ] `ROBLOX_OAUTH_REDIRECT_URI` - OAuth callback URL
- [ ] `ROBLOX_OAUTH_SCOPES` - Required scopes (comma-separated)

### Plugin & Studio (Medium - P2)
- [ ] `ROBLOX_PLUGIN_PORT` - Plugin port (default: 64989)
- [ ] `ROBLOX_STUDIO_PORT` - Studio port (default: 8765)
- [ ] `ROBLOX_API_BASE` - API base URL (default: https://api.roblox.com)

### Webhooks & Security (Medium - P2)
- [ ] `ROBLOX_WEBHOOK_URL` - Webhook endpoint
- [ ] `ROBLOX_WEBHOOK_SECRET` - Webhook signing secret

### Deployment (Low - P3)
- [ ] `ROBLOX_DEPLOYMENT_ENABLED` - Enable deployment (default: "false")
- [ ] `ROBLOX_AUTO_DEPLOY` - Auto-deploy on changes (default: "false")
- [ ] `ROBLOX_DEPLOY_BRANCH` - Deploy branch (default: "main")
- [ ] `ROBLOX_DEPLOY_KEY` - Deployment key

### Resource Limits (Low - P3)
- [ ] `ROBLOX_MAX_PARTS` - Max parts per environment (default: 10000)
- [ ] `ROBLOX_MAX_SCRIPTS` - Max scripts per environment (default: 100)

---

## Priority Classification

### P0 - Critical (Must Have for Launch)
- Database connections (Supabase)
- Redis cache
- JWT secrets
- API keys (OpenAI, etc.)
- CORS configuration
- Backend and frontend URLs

**Total P0 Variables:** ~40

### P1 - High (Required for Full Functionality)
- Clerk authentication
- Pusher real-time
- LangChain observability
- Supabase storage
- Celery configuration
- Roblox OAuth

**Total P1 Variables:** ~50

### P2 - Medium (Enhanced Features)
- Monitoring/logging
- Feature flags
- Performance tuning
- External integrations
- Development tools

**Total P2 Variables:** ~40

### P3 - Low (Optional/Future)
- Advanced monitoring
- Payment processing
- Marketing/analytics
- Vault secrets
- Additional integrations

**Total P3 Variables:** ~20

---

## Security Best Practices

### Secret Generation
```bash
# JWT Secret (32+ characters)
openssl rand -hex 32

# Database Password (32 characters)
openssl rand -base64 32

# Redis Password (24 characters)
openssl rand -base64 24

# Encryption Key (16 bytes hex)
openssl rand -hex 16
```

### Storage Locations
- **Render Secrets:** Environment variable groups in Render Dashboard
- **Vercel Secrets:** Project settings → Environment Variables
- **GitHub Secrets:** Repository Settings → Secrets and Variables → Actions
- **Local Development:** `.env` file (NEVER commit to git)

### Rotation Schedule
- **Critical secrets:** Every 90 days
- **API keys:** Per provider requirements
- **Database passwords:** Every 180 days
- **JWT secrets:** Every 365 days or on compromise

---

## Next Steps (Phase 2)

1. **Verify Existing Values:**
   - Check Render Dashboard for configured variables
   - Check Vercel project settings
   - Check GitHub Actions secrets

2. **Generate Missing Secrets:**
   - Use provided commands to generate secure secrets
   - Document generation date and expiration

3. **Configure Services:**
   - Set all P0 variables first
   - Test backend health endpoint
   - Test frontend build
   - Verify database connectivity

4. **Validate Integration:**
   - Test API endpoints
   - Test authentication flow
   - Test real-time features
   - Test Roblox integration

5. **Document Actual Values:**
   - Create secure documentation
   - Update Render environment groups
   - Update Vercel environment variables
   - Update GitHub secrets

---

## Audit Completed By
- **Agent:** Phase 1 Discovery Agent
- **Date:** 2025-11-10
- **Next Review:** After Phase 2 Configuration

---

**Note:** This audit is based on `.env.example`, `vercel.json`, `render.production.yaml`, and codebase analysis. Actual deployed values may differ and should be verified in Phase 2.
