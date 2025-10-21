# Vercel Deployment Guide

## Deployment Configuration Fixed - October 21, 2025

### Issues Resolved

1. **Removed `.vercel/` from `.vercelignore`** - Deployment metadata is now properly included
2. **Updated region** - Changed from `sfo1` to `pdx1` to match deployment infrastructure
3. **Updated API backend URL** - Changed from placeholder to `https://toolboxai-backend.onrender.com`

### Required Environment Variables

Before deploying to Vercel, you must configure these environment variables in your Vercel project settings:

#### Navigate to Vercel Dashboard
```
https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings/environment-variables
```

#### Required Variables (Production)

**Backend API Configuration:**
```bash
VITE_API_BASE_URL=https://toolboxai-backend.onrender.com
VITE_WS_URL=wss://toolboxai-backend.onrender.com
```

**Pusher Configuration (Real-time):**
```bash
VITE_PUSHER_KEY=your-pusher-app-key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth
VITE_ENABLE_PUSHER=true
```

**Supabase Configuration:**
```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

**Optional - Analytics & Monitoring:**
```bash
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

**Optional - Feature Flags:**
```bash
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_DEBUG_MODE=false
VITE_ENABLE_CLERK_AUTH=false
```

### Deployment Steps

#### 1. Set Environment Variables
```bash
# Login to Vercel CLI
vercel login

# Link to your project
vercel link

# Set production environment variables (example)
vercel env add VITE_API_BASE_URL production
# Enter: https://toolboxai-backend.onrender.com

vercel env add VITE_PUSHER_KEY production
# Enter: your-pusher-app-key

# Repeat for all required variables
```

#### 2. Deploy to Vercel
```bash
# Deploy to production
vercel --prod

# Or deploy preview
vercel
```

#### 3. Alternative: Deploy via GitHub Integration
1. Push to your main branch: `git push origin feat/supabase-backend-enhancement`
2. Vercel will automatically deploy
3. Check deployment status at: https://vercel.com/grayghostdevs-projects/toolbox-production-final

### Vercel Project Configuration

**Current Configuration (`vercel.json`):**
- **Build Command:** `npm run dashboard:build`
- **Output Directory:** `apps/dashboard/dist`
- **Install Command:** `npm ci --include=dev --workspaces`
- **Region:** Portland, USA West (pdx1)
- **Node Version:** 22
- **Framework:** None (Vite SPA)

### API Backend Configuration

The frontend is configured to proxy API requests to your backend:

**Rewrite Rule:**
```json
{
  "source": "/api/:path*",
  "destination": "https://toolboxai-backend.onrender.com/api/:path*"
}
```

**Important:** Update this URL in `vercel.json` if your backend is hosted elsewhere.

### SPA Routing Configuration

All non-API routes are rewritten to `/index.html` for client-side routing:

```json
{
  "source": "/:path((?!api|assets|_next|favicon.ico).*)*",
  "destination": "/index.html"
}
```

### Security Headers

Production deployment includes security headers:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: camera=(), microphone=(), geolocation=()

### Build Optimization

**Large Chunks Warning:**
The build shows some chunks larger than 200 kB. Consider:
1. Code splitting with dynamic imports
2. Lazy loading heavy components (Three.js, charts)
3. Using `build.rollupOptions.output.manualChunks` in Vite config

**Current Large Chunks:**
- `lazy-three-core.js` - 1,235 kB (Three.js)
- `lazy-charts.js` - 458 kB (Charts library)
- `critical-react.js` - 334 kB (React core)

These are already code-split and load on demand.

### Troubleshooting

#### Deployment Failed During "Deploying outputs"
**Solution Applied:**
1. ✅ Removed `.vercel/` from `.vercelignore`
2. ✅ Updated region to match deployment infrastructure
3. ✅ Fixed backend API URL placeholder

#### Build Succeeds but Runtime Errors
**Check:**
1. Environment variables are set in Vercel dashboard
2. Backend API is accessible from Vercel's infrastructure
3. CORS is properly configured on backend
4. Pusher credentials are valid

#### API Requests Failing (404/CORS)
**Check:**
1. Backend URL in `vercel.json` matches actual backend
2. Backend accepts requests from Vercel domain
3. API endpoints start with `/api/` prefix

### Vercel CLI Commands

```bash
# Check deployment status
vercel ls

# View deployment logs
vercel logs <deployment-url>

# Inspect environment variables
vercel env ls

# Pull environment variables locally
vercel env pull .env.vercel

# Rollback to previous deployment
vercel rollback <deployment-url>
```

### Production Checklist

Before deploying to production:

- [ ] All environment variables configured in Vercel dashboard
- [ ] Backend API URL updated in `vercel.json`
- [ ] Backend CORS allows Vercel production domain
- [ ] Pusher app configured and credentials set
- [ ] Supabase project created and configured
- [ ] Error tracking (Sentry) configured
- [ ] Database migrations applied
- [ ] Backend deployed and accessible
- [ ] DNS configured (if using custom domain)
- [ ] SSL certificate active

### Next Steps

1. **Set all required environment variables** in Vercel dashboard
2. **Update backend API URL** if different from `toolboxai-backend.onrender.com`
3. **Trigger new deployment** by pushing to GitHub or running `vercel --prod`
4. **Monitor deployment logs** for any remaining issues
5. **Test production deployment** after successful deploy

### Support

- **Vercel Dashboard:** https://vercel.com/grayghostdevs-projects/toolbox-production-final
- **Deployment Logs:** Available in Vercel dashboard under deployments
- **Environment Variables:** https://vercel.com/docs/concepts/projects/environment-variables
- **Build Configuration:** https://vercel.com/docs/build-step

---

**Last Updated:** October 21, 2025
**Configuration Version:** v2
**Deployment Status:** Ready for deployment after environment variables are set
