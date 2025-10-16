# Vercel Deployment - Quick Start Guide

Quick reference for deploying ToolboxAI Dashboard to Vercel.

## 🚀 One-Time Setup (5 minutes)

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Link Project

```bash
# From project root
vercel link
```

Choose:
- **Scope**: Your Vercel account/team
- **Link to existing project?**: No
- **Project name**: `toolboxai-dashboard` (or your preferred name)
- **Directory**: `.` (current directory)

### 4. Set Environment Variables

Go to [Vercel Dashboard](https://vercel.com/dashboard) → Your Project → Settings → Environment Variables

Add these **required** variables:

```bash
VITE_API_BASE_URL=https://your-backend-api.com
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_CLUSTER=us2
VITE_ENABLE_PUSHER=true
```

**Optional variables** (if needed):
```bash
VITE_ENABLE_CLERK_AUTH=false
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_SUPABASE_URL=https://...supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_SENTRY_DSN=https://...@sentry.io/...
```

## 📦 Deploy Commands

### Preview Deployment (Recommended for testing)

```bash
# Using deployment script (recommended)
./scripts/deployment/deploy-vercel.sh

# Or using Vercel CLI directly
vercel
```

### Production Deployment

```bash
# Using deployment script (recommended)
./scripts/deployment/deploy-vercel.sh --production

# Or using Vercel CLI directly
vercel --prod
```

### Skip Tests (For quick deployments)

```bash
./scripts/deployment/deploy-vercel.sh --skip-tests
```

## 🔍 Check Deployment Status

```bash
# View recent deployments
vercel ls

# View deployment logs
vercel logs

# Inspect specific deployment
vercel inspect <deployment-url>
```

## ⚙️ Configuration Files

The deployment uses these configuration files:

- **`vercel.json`** - Main Vercel configuration
- **`.env.vercel.example`** - Environment variables template
- **`apps/dashboard/vite.config.js`** - Build configuration
- **`package.json`** - Build commands and dependencies

## 🔗 Important URLs

After deployment, you'll get:

- **Preview**: `https://toolboxai-dashboard-<hash>.vercel.app`
- **Production**: `https://toolboxai-dashboard.vercel.app`
- **Custom Domain**: Set up in Vercel Dashboard → Domains

## 🛠️ Common Issues & Solutions

### Issue: Build fails with "Module not found"

**Solution**: Ensure all dependencies are installed
```bash
npm install
npm run dashboard:build  # Test locally first
```

### Issue: API calls return CORS errors

**Solution**: Update backend CORS configuration to allow Vercel domain
```python
# In your FastAPI backend
allow_origins=[
    "https://toolboxai-dashboard.vercel.app",
    "https://*.vercel.app"  # For preview deployments
]
```

### Issue: Environment variables not working

**Solution**: Rebuild deployment after adding variables
```bash
vercel --prod --force  # Force rebuild
```

### Issue: Pusher connection fails

**Solution**:
1. Verify Pusher credentials in Vercel environment variables
2. Check Pusher app allows connections from Vercel's IPs
3. Test at: https://dashboard.pusher.com/apps/YOUR_APP_ID/debug_console

## 📊 Monitor Your Deployment

### Vercel Dashboard
- **Analytics**: View page performance, Core Web Vitals
- **Deployments**: See all deployment history
- **Logs**: Real-time and historical logs

### Performance Metrics
```bash
# Test deployment speed
curl -w "@curl-format.txt" -o /dev/null -s https://your-deployment.vercel.app
```

Create `curl-format.txt`:
```
time_namelookup: %{time_namelookup}s
time_connect: %{time_connect}s
time_appconnect: %{time_appconnect}s
time_pretransfer: %{time_pretransfer}s
time_redirect: %{time_redirect}s
time_starttransfer: %{time_starttransfer}s
time_total: %{time_total}s
```

## 🔄 Automatic Deployments

Vercel automatically deploys when you:

- **Push to `main` branch** → Production deployment
- **Create a Pull Request** → Preview deployment
- **Push to any branch** → Preview deployment

Configure in: **Settings** → **Git** → **Automatic Deployments**

## 📚 Additional Resources

- **Full Documentation**: See `docs/deployment/VERCEL_DEPLOYMENT.md`
- **Environment Template**: See `.env.vercel.example`
- **Vercel Docs**: https://vercel.com/docs
- **Dashboard Status**: https://www.vercel-status.com

## 🆘 Get Help

- **Vercel Support**: support@vercel.com
- **Vercel Discord**: https://vercel.com/discord
- **Project Issues**: GitHub Issues

## ✅ Pre-Deployment Checklist

Before each deployment:

- [ ] All tests passing locally: `npm run dashboard:test`
- [ ] Build successful locally: `npm run dashboard:build`
- [ ] Environment variables configured in Vercel
- [ ] Backend API is accessible
- [ ] Pusher credentials are correct
- [ ] Git commits pushed to repository
- [ ] CORS configured on backend for Vercel domain

## 🎯 Quick Commands Reference

```bash
# Deploy preview
vercel

# Deploy production
vercel --prod

# View deployments
vercel ls

# View logs
vercel logs

# Set environment variable
vercel env add VARIABLE_NAME production

# Pull environment variables locally
vercel env pull

# Remove deployment
vercel rm <deployment-url>

# Open deployment in browser
vercel open

# Get deployment alias
vercel alias ls
```

---

**Last Updated**: October 16, 2025
**Vercel CLI**: Latest
**Node**: 22.x
**Framework**: Vite 6.0.1 + React 19.1.0
