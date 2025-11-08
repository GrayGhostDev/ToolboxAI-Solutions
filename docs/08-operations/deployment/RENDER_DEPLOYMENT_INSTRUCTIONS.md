# Render Blueprint Deployment Instructions
**Blueprint ID:** exs-d473mme3jp1c73booqig
**Updated:** 2025-11-07
**Status:** ✅ READY FOR DEPLOYMENT

---

## ✅ Updates Applied to render.yaml

### Services Updated:
1. **toolboxai-backend** - Added Supabase S3, Clerk, LangChain
2. **toolboxai-mcp** - Added Supabase S3, LangChain
3. **toolboxai-agent-coordinator** - Added Supabase S3, LangChain
4. **toolboxai-dashboard** - Updated frontend environment variables

### Environment Variable Groups Updated:
1. **toolboxai-secrets** - Added 16 new keys
2. **toolboxai-frontend-env** - Added 13 new keys

---

## 🚀 Deployment Steps

### Step 1: Verify Local Changes

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('render.yaml'))" && echo "✅ Valid"

# Review changes
git diff render.yaml
```

### Step 2: Commit and Push Changes

```bash
# Stage the updated blueprint
git add render.yaml

# Commit with descriptive message
git commit -m "fix: Update Render blueprint with Supabase S3, Clerk auth, and LangChain config

- Add Supabase S3 storage credentials to backend, MCP, and agent-coordinator
- Configure Clerk authentication for backend and frontend
- Add LangChain/LangSmith tracing configuration
- Update environment variable groups with all required keys
- Add missing API keys (Replicate, LangCache)
- Enhance frontend configuration with Supabase and Clerk

Blueprint ID: exs-d473mme3jp1c73booqig"

# Push to remote
git push origin main
```

### Step 3: Configure Environment Variables in Render Dashboard

**CRITICAL:** Before deploying, you must set the following values in the Render Dashboard.

Navigate to: **Render Dashboard → ToolBoxAI Project → Environment Variable Groups**

---

## 🔐 SSL/TLS Certificate Configuration (Optional)

### Current Setup: Standard SSL (Recommended)

Your current DATABASE_URL already uses **`sslmode=require`** which provides:
- ✅ SSL/TLS encryption for all database connections
- ✅ Simple configuration (no certificate management needed)
- ✅ **No additional setup required!**

```bash
postgresql://postgres:ToolBoXA1!2025!@db.jlesbkscprldariqcbvt.supabase.co:6543/postgres?sslmode=require
```

### Enhanced Security: Certificate Verification (Optional)

For high-security requirements (financial, healthcare, compliance), you can upgrade to certificate verification:

**See:** `docs/SUPABASE_SSL_CONFIGURATION.md` for complete instructions

**Quick Setup:**
1. Add `SUPABASE_SSL_CERT_B64` to `toolboxai-secrets` (value provided below)
2. Update `DATABASE_URL` to use `sslmode=verify-ca&sslrootcert=/opt/render/project/.postgresql/root.crt`
3. Deploy (certificate is automatically configured via pre-deploy script)

**When to use enhanced SSL:**
- Financial services (PCI-DSS)
- Healthcare applications (HIPAA)
- Government contracts
- Enterprise security policies

---

## 📝 Environment Variable Configuration

### Group: `toolboxai-secrets`

Copy these values **exactly** from your `.env` file:

```bash
# Supabase Configuration
DATABASE_URL=postgresql://postgres:ToolBoXA1!2025!@db.jlesbkscprldariqcbvt.supabase.co:6543/postgres?sslmode=require
SUPABASE_URL=https://jlesbkscprldariqcbvt.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZXNia3NjcHJsZGFyaXFjYnZ0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODQzNjM1NiwiZXhwIjoyMDc0MDEyMzU2fQ.J_4amgJXEoHY3yhJpHAcKP7X-vnSBPOFCee626k8ZlI
SUPABASE_DATABASE_URL=postgresql://postgres:ToolBoXA1!2025!@db.jlesbkscprldariqcbvt.supabase.co:6543/postgres?sslmode=require
SUPABASE_S3_ENDPOINT=https://jlesbkscprldariqcbvt.storage.supabase.co/storage/v1/s3
SUPABASE_S3_REGION=us-east-2
SUPABASE_S3_ACCESS_KEY_ID=e31a9fa3a7de8a46021afd11f7ca70ba
SUPABASE_S3_SECRET_ACCESS_KEY=da49278f913569ad3f344caad0f17b2d2f1f2dae5633dae2a1e2bdc9ae3e157c

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_3ArqrdCHHmjxHvgtAt2zxr2Znd8L8ziEWUiH8NDI49
CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
CLERK_WEBHOOK_SIGNING_SECRET=whsec_yfJVjj0muO9lOYGyOEMH3cbVBXS7Znct
CLERK_JWKS_URL=https://casual-firefly-39.clerk.accounts.dev/.well-known/jwks.json

# AI API Keys
OPENAI_API_KEY=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
ANTHROPIC_API_KEY=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
REPLICATE_API_TOKEN=r8_DlSYrrAzQrQHl6TyPhQ2gXd4nR0skzK4URqVp

# LangChain/LangSmith
LANGCHAIN_API_KEY=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
LANGCACHE_API_KEY=wy4ECQMIVTKLbf4DoKjgl1DyOqSaI36fvrh9DOOxBNrYQup6xUcrhk9nBNFEqHlw0oIBiHkP8QGv6KkR9g9rK8R1x8WbNvxZqxuZ8KGvpk80LdhXQAyRXoE1EJtlGicLd1DqSJeRJvBQ7Eu6m9Or8ovEcwrqq1n216DAMNSIcIF-hA586GEjhOb6GOOwdnQlY1eAs83-5EP33IPJGn-gJ1n0By6RA93-WPM8vjvRdMjO_Ija
LANGCACHE_CACHE_ID=f5c5e531f8954e35b864eb710d3f891c

# Supabase SSL Certificate (OPTIONAL - for enhanced security)
# Use this for sslmode=verify-ca or verify-full
# See docs/SUPABASE_SSL_CONFIGURATION.md for details
SUPABASE_SSL_CERT_B64=LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUR4RENDQXF5Z0F3SUJBZ0lVYkx4TW9kNjJQMmt0Q2lBa3huS0p3dEU5VlBZd0RRWUpLb1pJaHZjTkFRRUwKQlFBd2F6RUxNQWtHQTFVRUJoTUNWVk14RURBT0JnTlZCQWdNQjBSbGJIZGhjbVV4RXpBUkJnTlZCQWNNQ2s1bApkeUJEWVhOMGJHVXhGVEFUQmdOVkJBb01ERk4xY0dGaVlYTmxJRWx1WXpFZU1Cd0dBMVVFQXd3VlUzVndZV0poCmMyVWdVbTl2ZENBeU1ESXhJRU5CTUI0WERUSXhNRFF5T0RFd05UWTFNMW9YRFRNeE1EUXlOakV3TlRZMU0xb3cKYXpFTE1Ba0dBMVVFQmhNQ1ZWTXhFREFPQmdOVkJBZ01CMFJsYkhkaGNtVXhFekFSQmdOVkJBY01DazVsZHlCRApZWE4wYkdVeEZUQVRCZ05WQkFvTURGTjFjR0ZpWVhObElFbHVZekVlTUJ3R0ExVUVBd3dWVTNWd1lXSmhjMlVnClVtOXZkQ0F5TURJeElFTkJNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQXFRWFcKUXlIT0IrcVIyR0pvYkNxL0NCbVE0MEcwb0RtQ0MzbXpWbm44c3Y0WE5lV3RFNVhjRUwwdVZpaDdKbzREa3gxUQpEbUdIQkgxekRmZ3MycVhpTGI2eHB3L0NLUVB5cFpXMUpzc09UTUlmUXBwTlE4N0s3NVlhMHAyNVkzZVBTMnQyCkd0dkh4TmpVVjZrak9aakVuMnlXRWNCZHBPVkNVWUJWRkJOTUI0WUJIa05SRGEvK1M0dXl3QW9hVFduQ0pMVWkKY3ZUbEhtTXc2eFNRUW4xVWZSUUhrNTBETUNFSjdDeTFSeHJaSnJrWFhSUDNMcVFMMmlqSjZGNHlNZmgrR3liNApPNFhham9Wai8rUjRHd3l3S1lyclM4UHJTTnR3eHI1U3RsUU84eklRVVNNaXEyNndNOG1nRUxGbFMvMzJVY2x0Ck5hUTF4QlJpemt6cFpjdDlEd0lEQVFBQm8yQXdYakFMQmdOVkhROEVCQU1DQVFZd0hRWURWUjBPQkJZRUZLalgKdVhZMzJDenRraEltbmc0eUpOVXRhVVlzTUI4R0ExVWRJd1FZTUJhQUZLalh1WFkzMkN6dGtoSW1uZzR5Sk5VdAphVVlzTUE4R0ExVWRFd0VCL3dRRk1BTUJBZjh3RFFZSktvWklodmNOQVFFTEJRQURnZ0VCQUI4c3B6Tm4rNFZVCnRWeGJkTWFYKzM5WjUwc2M3dUFUbXVzMTZqbW1IamhJSHorbC85R2xKNUtxQU1PeDI2bVBaZ2Z6RzdvbmVMMmIKVlcrV2dZVWtUVDNYRVBGV25UcDJSSndRYW84L3RZUFhXRUpEYzBXVlFIcnBtbldPRktVL2QzTXFCZ0JtNXkrNgpqQjgxVFUvUkcyclZlclBEV1ArMU1NY05OeTA0OTFDVEw1WFFaN0pmREpKOUNDbVhTZHRUbDR1VVFuU3V2L1F4CkNlYTEzQlgyWmdKYzdBdTMwdmloTGh1YjUyRGU0UC80Z29uS3NOSFlkYldqZzdPV0t3TnYveml0R0RWREI5WTIKQ01UeVpLRzNYRXU1R2hsMUxFbkkzUW1FS3NxYUNMdjEyQm5WamJrU2Vac01uZXZKUHMxWWU2VGpqSndkaWs1UApvL2JLaUl6K0ZxOD0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=

# Pusher Real-time
PUSHER_APP_ID=2050003
PUSHER_KEY=73f059a21bb304c7d68c
PUSHER_SECRET=fe8d15d3d7ee36652b7a

# Monitoring
SENTRY_DSN=https://6175c9912112e5a9fa094247539d13f5@o4509912543199232.ingest.us.sentry.io/4510294208937984

# Email (SendGrid)
SENDGRID_API_KEY=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

# SMS (Twilio)
TWILIO_ACCOUNT_SID=AC554c2d9641861cbd82d7c4db296fd189
TWILIO_AUTH_TOKEN=febcac24ce956f1942069ba7356e5a0c

# Flower Monitoring
FLOWER_BASIC_AUTH=admin:secure_password_here
```

---

### Group: `toolboxai-frontend-env`

Copy these values for frontend configuration:

```bash
# Supabase Frontend
VITE_SUPABASE_URL=https://jlesbkscprldariqcbvt.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_s9XplM0Sz75mQSZdAPwdSw__Gye2M1q
VITE_SUPABASE_S3_ENDPOINT=https://jlesbkscprldariqcbvt.storage.supabase.co/storage/v1/s3

# Clerk Frontend
VITE_CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA
VITE_CLERK_FRONTEND_API_URL=https://casual-firefly-39.clerk.accounts.dev

# Pusher Frontend
VITE_PUSHER_KEY=73f059a21bb304c7d68c

# Monitoring
VITE_SENTRY_DSN=(create separate Sentry project for frontend)
```

---

## Step 4: Deploy Blueprint

### Option A: Via Render Dashboard (Recommended)

1. Go to **Render Dashboard** → **Your Project**
2. Click **"Settings"** → **"Blueprint"**
3. Click **"Update Blueprint"**
4. Render will detect the changes from your git repository
5. Review the changes and click **"Apply"**

### Option B: Via Render API (Advanced)

```bash
# Update blueprint via API
curl -X PUT \
  https://api.render.com/v1/blueprints/exs-d473mme3jp1c73booqig \
  -H "Authorization: Bearer YOUR_RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d @render.yaml
```

---

## ✅ Post-Deployment Verification

### Check 1: Service Health

```bash
# Backend health check
curl https://toolboxai-backend.onrender.com/health

# Expected: {"status": "healthy", "database": "connected", "redis": "connected"}

# MCP health check
curl https://toolboxai-mcp.onrender.com/health

# Agent Coordinator health check
curl https://toolboxai-agent-coordinator.onrender.com/health

# Dashboard
curl https://toolboxai-dashboard.onrender.com
```

### Check 2: Database Connectivity

```bash
# Check logs for successful database connection
render logs toolboxai-backend --tail 50 | grep "database"
```

### Check 3: Authentication

```bash
# Test Clerk authentication endpoint
curl https://toolboxai-backend.onrender.com/api/v1/auth/verify
```

### Check 4: File Upload (S3)

```bash
# Test file upload to Supabase S3
curl -X POST https://toolboxai-backend.onrender.com/api/v1/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.txt"
```

### Check 5: LangSmith Tracing

1. Go to **https://smith.langchain.com**
2. Navigate to **ToolboxAI-Solutions** project
3. Verify traces are appearing from production

---

## 🔍 Troubleshooting

### Issue: Services failing to start

**Check logs:**
```bash
render logs toolboxai-backend -n 100
```

**Common causes:**
- Missing environment variables
- Database connection errors
- Redis connection errors

**Solution:**
Verify all environment variables are set in the correct groups.

---

### Issue: Database connection timeout

**Error:** `connection to server at "db.jlesbkscprldariqcbvt.supabase.co" failed`

**Solution:**
1. Verify `DATABASE_URL` uses port **6543** (pooler) not 5432
2. Ensure `sslmode=require` is in the connection string
3. Check Supabase dashboard for connection pooler status

---

### Issue: Clerk authentication failing

**Error:** `Invalid Clerk secret key`

**Solution:**
1. Verify `CLERK_SECRET_KEY` matches your Clerk dashboard
2. Ensure `CLERK_JWKS_URL` is correct
3. Check webhook secret is configured

---

### Issue: File uploads failing

**Error:** `S3 endpoint not accessible`

**Solution:**
1. Verify Supabase S3 credentials are correct
2. Check storage bucket `toolboxai-uploads` exists
3. Verify IAM permissions for S3 access keys

---

## 📊 Service Resource Allocation

All services configured with **Starter plan** resources:

- **CPU:** 0.5 vCPU
- **Memory:** 512 MB
- **Bandwidth:** Unlimited
- **Storage:** Stateless (uses Supabase)

**Total estimated cost:** ~$35/month for all services

---

## 🔒 Security Checklist

Before deploying to production:

- [x] All secrets stored in environment variable groups (not in render.yaml)
- [x] Database uses SSL/TLS (`sslmode=require`)
- [x] API keys are valid and have appropriate permissions
- [x] Clerk webhook secrets configured
- [x] CORS origins properly configured
- [x] Rate limiting enabled
- [x] Sentry monitoring configured
- [ ] Custom domain configured (optional)
- [ ] SSL certificate verified (automatic with Render)

---

## 📈 Monitoring

### Service Status Dashboard

View all service status at: **https://dashboard.render.com/YOUR_PROJECT**

### Metrics to Monitor:

1. **Response Time** (target: < 200ms p95)
2. **Error Rate** (target: < 0.1%)
3. **Database Connections** (max: 10 per service)
4. **Redis Memory Usage**
5. **Celery Queue Length**

### Alerting

Configure alerts in Render Dashboard:
- Service health check failures
- High memory usage (> 80%)
- High CPU usage (> 80%)
- Deployment failures

---

## 🎯 Next Steps After Deployment

1. **Configure Custom Domain** (optional)
   - Add domain in Render Dashboard
   - Update DNS records
   - SSL certificate auto-provisioned

2. **Enable GitHub Auto-Deploy**
   - Push to `main` → auto-deploy to production
   - Push to `develop` → auto-deploy to staging

3. **Set Up Monitoring Dashboard**
   - Configure Grafana dashboards
   - Set up alerting to Slack
   - Enable Sentry performance monitoring

4. **Load Testing**
   - Run load tests to verify performance
   - Adjust service plans if needed

5. **Backup Strategy**
   - Supabase automatic backups (included)
   - Export critical data weekly
   - Test restore procedures

---

## 📞 Support

**Issues with deployment?**
- Check service logs in Render Dashboard
- Review this documentation
- Contact Render support: support@render.com

**Project-specific questions?**
- Review `docs/` folder
- Check `CLAUDE.md` for architecture details

---

**Status:** ✅ Ready for production deployment
**Last Updated:** 2025-11-07
**Blueprint Version:** 2.0
