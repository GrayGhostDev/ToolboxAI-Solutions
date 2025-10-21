# Production Deployment Guide

## Architecture Overview

**Frontend:** Vercel (SPA - React/Vite)
**Backend:** Render.com (FastAPI/Python)
**Database:** Supabase (PostgreSQL)
**Authentication:** Clerk
**Real-time:** Pusher Channels

---

## Step 1: Deploy Backend to Render

### 1.1 Push Code to GitHub

```bash
git add .
git commit -m "feat(deploy): configure production deployment with Supabase and Clerk"
git push origin feat/supabase-backend-enhancement
```

### 1.2 Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure service:
   - **Name:** `toolboxai-backend`
   - **Region:** Oregon (US West)
   - **Branch:** `feat/supabase-backend-enhancement` (or `main`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn apps.backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Starter (or higher)

### 1.3 Configure Environment Variables in Render

Add these environment variables in Render dashboard:

#### Supabase Configuration
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
DATABASE_URL=postgresql://user:password@host:port/database
```

#### Clerk Authentication
```bash
CLERK_SECRET_KEY=sk_test_your-clerk-secret-key
CLERK_PUBLISHABLE_KEY=pk_test_your-clerk-publishable-key
```

#### JWT Configuration
```bash
JWT_SECRET_KEY=your-secure-random-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### Pusher Configuration
```bash
PUSHER_APP_ID=your-pusher-app-id
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2
```

#### CORS Configuration
```bash
CORS_ORIGINS=https://toolbox-production-final.vercel.app,https://toolbox-production-final-*.vercel.app
```

#### Optional Services
```bash
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
SENDGRID_API_KEY=SG.your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@toolboxai.com
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

#### Environment Settings
```bash
ENVIRONMENT=production
DEBUG=false
PYTHONPATH=/opt/render/project/src
```

### 1.4 Deploy Backend

1. Click "Create Web Service"
2. Wait for deployment to complete (usually 3-5 minutes)
3. Note your backend URL: `https://toolboxai-backend.onrender.com`

### 1.5 Verify Backend Health

```bash
curl https://toolboxai-backend.onrender.com/health
```

---

## Step 2: Configure Supabase Database

### 2.1 Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Create new project
3. Note your credentials:
   - **URL:** `https://your-project.supabase.co`
   - **Anon Key:** From Settings → API
   - **Service Role Key:** From Settings → API
   - **Database URL:** From Settings → Database

### 2.2 Run Database Migrations

```bash
# From your local environment
export DATABASE_URL="your-supabase-database-url"

# Run migrations (if using Alembic)
alembic upgrade head

# Or apply schema directly
psql $DATABASE_URL < database/schema.sql
```

### 2.3 Configure Row Level Security (RLS)

Enable RLS on all tables in Supabase dashboard:
- Users table
- Content tables
- Progress tables
- Any other sensitive tables

---

## Step 3: Set Up Clerk Authentication

### 3.1 Create Clerk Application

1. Go to [Clerk Dashboard](https://dashboard.clerk.com/)
2. Create new application
3. Configure settings:
   - **Application Name:** ToolboxAI Solutions
   - **Social Login:** Enable Google, GitHub (optional)
   - **Session Settings:** Configure as needed

### 3.2 Get Clerk Keys

From Clerk Dashboard → API Keys:
- **Publishable Key:** `pk_test_...` or `pk_live_...`
- **Secret Key:** `sk_test_...` or `sk_live_...`

### 3.3 Configure Clerk Webhooks

Add webhook endpoint in Clerk:
- **URL:** `https://toolboxai-backend.onrender.com/api/v1/auth/clerk/webhook`
- **Events:** `user.created`, `user.updated`, `user.deleted`

---

## Step 4: Configure Pusher

### 4.1 Create Pusher App

1. Go to [Pusher Dashboard](https://dashboard.pusher.com/)
2. Create new app
3. Configure:
   - **Name:** ToolboxAI Production
   - **Cluster:** us2
   - **Enable client events:** Yes

### 4.2 Get Pusher Credentials

From App Keys:
- **App ID**
- **Key**
- **Secret**
- **Cluster**

---

## Step 5: Deploy Frontend to Vercel

### 5.1 Push Latest Frontend Code

```bash
git add apps/dashboard
git commit -m "feat(dashboard): update for production deployment"
git push origin feat/supabase-backend-enhancement
```

### 5.2 Configure Vercel Project

The project is already configured. Verify settings:
- **Framework:** Vite
- **Build Command:** `npm run dashboard:build`
- **Output Directory:** `apps/dashboard/dist`
- **Install Command:** `npm ci --include=dev --workspaces`

### 5.3 Set Environment Variables in Vercel

Go to [Vercel Dashboard](https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings/environment-variables)

#### Backend Configuration
```bash
VITE_API_BASE_URL=https://toolboxai-backend.onrender.com
VITE_WS_URL=wss://toolboxai-backend.onrender.com
```

#### Clerk Authentication
```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_live_your-clerk-publishable-key
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your-clerk-publishable-key
VITE_ENABLE_CLERK_AUTH=true
```

#### Supabase Database
```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

#### Pusher Real-time
```bash
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth
VITE_ENABLE_PUSHER=true
```

#### Optional Analytics
```bash
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### 5.4 Trigger Deployment

Push to GitHub will auto-deploy, or manually trigger:

```bash
# Using Vercel CLI
vercel --prod

# Or push to trigger auto-deployment
git push origin feat/supabase-backend-enhancement
```

---

## Step 6: Verification & Testing

### 6.1 Backend Health Check

```bash
curl https://toolboxai-backend.onrender.com/health

# Expected response:
# {"status":"healthy","timestamp":"...","database":"connected"}
```

### 6.2 Frontend Access

Visit: `https://toolbox-production-final.vercel.app`

Expected:
- ✅ Page loads without errors
- ✅ Clerk authentication widget appears
- ✅ Can sign in/sign up
- ✅ Dashboard loads after authentication

### 6.3 API Connectivity

```bash
# Test API from frontend
curl https://toolbox-production-final.vercel.app/api/v1/health

# Should proxy to backend and return health status
```

### 6.4 Real-time Features

1. Open browser console
2. Navigate to dashboard
3. Check for Pusher connection:
```
Pusher : State changed : connecting -> connected
```

---

## Step 7: Post-Deployment Configuration

### 7.1 Configure Custom Domain (Optional)

#### Vercel Domain
1. Go to Vercel → Settings → Domains
2. Add your custom domain (e.g., `app.toolboxai.com`)
3. Configure DNS records as instructed

#### Render Domain
1. Go to Render → Settings → Custom Domains
2. Add API subdomain (e.g., `api.toolboxai.com`)
3. Update VITE_API_BASE_URL in Vercel

### 7.2 Enable Monitoring

#### Sentry
1. Create Sentry project
2. Add DSN to both Render and Vercel environment variables
3. Verify error tracking works

#### Render Monitoring
- Enable auto-deploy on push
- Set up notification for failed deployments
- Configure health check notifications

#### Vercel Analytics
- Enable Vercel Analytics in dashboard
- Review Web Vitals metrics

### 7.3 Security Hardening

#### CORS
Verify CORS_ORIGINS in Render only includes:
- Production Vercel domain
- Preview deployment pattern

#### Rate Limiting
- Configure rate limits in backend
- Add rate limiting middleware if needed

#### Secrets Rotation
Set reminders to rotate:
- JWT secrets (quarterly)
- API keys (when compromised)
- Database passwords (semi-annually)

---

## Troubleshooting

### Backend Won't Start

**Check Render logs:**
```bash
# Via Render dashboard or CLI
render logs
```

**Common issues:**
- Missing environment variables
- Database connection failures
- Import errors (check PYTHONPATH)

**Solutions:**
1. Verify all required env vars are set
2. Check DATABASE_URL format
3. Ensure requirements.txt is complete

### Frontend Can't Connect to Backend

**Check CORS configuration:**
```bash
# Backend should allow your Vercel domain
CORS_ORIGINS=https://toolbox-production-final.vercel.app
```

**Verify API proxy:**
- Check `vercel.json` rewrites configuration
- Ensure backend URL is correct in env vars

### Clerk Authentication Fails

**Check Clerk configuration:**
1. Verify publishable key matches environment (test vs live)
2. Check allowed domains in Clerk dashboard
3. Ensure webhook endpoint is accessible

### Pusher Connection Issues

**Verify Pusher configuration:**
1. Check cluster matches (usually `us2`)
2. Verify app key is correct
3. Ensure backend auth endpoint works: `/pusher/auth`

### Database Connection Errors

**Check Supabase:**
1. Verify DATABASE_URL format
2. Check connection pooler settings
3. Ensure IP allowlist includes Render IPs (or disable)

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Environment variables documented
- [ ] Database migrations ready
- [ ] Secrets rotated
- [ ] Dependencies updated

### Render Backend
- [ ] Service created
- [ ] Environment variables configured
- [ ] Deployment successful
- [ ] Health check passing
- [ ] Logs clean (no errors)

### Vercel Frontend
- [ ] Environment variables configured
- [ ] Build successful
- [ ] Deployment live
- [ ] No console errors
- [ ] Authentication working

### Services
- [ ] Supabase database accessible
- [ ] Clerk authentication configured
- [ ] Pusher real-time working
- [ ] Email service configured (SendGrid)
- [ ] Error monitoring active (Sentry)

### Testing
- [ ] Can sign up/sign in
- [ ] Dashboard loads correctly
- [ ] API calls work
- [ ] Real-time updates work
- [ ] Mobile responsive

### Production
- [ ] Custom domain configured
- [ ] SSL certificates active
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Team notified

---

## Support & Resources

**Render:**
- Dashboard: https://dashboard.render.com/
- Docs: https://render.com/docs
- Support: support@render.com

**Vercel:**
- Dashboard: https://vercel.com/dashboard
- Docs: https://vercel.com/docs
- Support: https://vercel.com/support

**Supabase:**
- Dashboard: https://app.supabase.com/
- Docs: https://supabase.com/docs
- Support: https://supabase.com/support

**Clerk:**
- Dashboard: https://dashboard.clerk.com/
- Docs: https://clerk.com/docs
- Support: support@clerk.com

**Pusher:**
- Dashboard: https://dashboard.pusher.com/
- Docs: https://pusher.com/docs
- Support: support@pusher.com

---

**Last Updated:** October 21, 2025
**Version:** 1.0.0
**Status:** Production Ready
