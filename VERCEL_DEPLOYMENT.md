# Vercel Deployment Guide - ToolboxAI Solutions

## 🚀 Quick Start

Your repository is now configured for **Vercel deployment**! Follow these steps to deploy your dashboard.

---

## 📋 Prerequisites

- GitHub account with access to the repository
- Vercel account (free tier available at https://vercel.com)
- Backend API deployed and accessible (for API calls)

---

## 🔧 Deployment Steps

### 1. **Import Project to Vercel**

1. Go to [Vercel Dashboard](https://vercel.com/new)
2. Click **"Import Project"**
3. Select **"Import Git Repository"**
4. Choose **GitHub** as your Git provider
5. Search for and select: **`GrayGhostDev/ToolboxAI-Solutions`**
6. Click **"Import"**

### 2. **Configure Build Settings**

Vercel will auto-detect the configuration from `vercel.json`, but verify:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `.` (root) |
| **Build Command** | `cd apps/dashboard && npm install && npm run build` |
| **Output Directory** | `apps/dashboard/dist` |
| **Install Command** | `npm install --workspace=apps/dashboard` |
| **Node.js Version** | 22.x |

### 3. **Configure Environment Variables**

⚠️ **CRITICAL**: Set these in Vercel Dashboard under **Settings → Environment Variables**

#### Required Variables:

```bash
# API Configuration (REQUIRED)
VITE_API_BASE_URL=https://your-backend-api.com
VITE_WS_URL=wss://your-backend-api.com

# Pusher Configuration (REQUIRED for realtime features)
VITE_PUSHER_KEY=your-pusher-app-key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/api/pusher/auth
VITE_PUSHER_SSL=true

# Feature Flags
VITE_ENABLE_PUSHER=true
VITE_ENABLE_WEBSOCKET=false
VITE_ENABLE_GAMIFICATION=true
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_MCP=true
VITE_ENABLE_AGENTS=true
VITE_ENABLE_ROBLOX=true
VITE_ENABLE_GHOST=true
VITE_ENABLE_AI_CHAT=true

# Environment
NODE_ENV=production
VITE_DEBUG_MODE=false
VITE_MOCK_API=false
```

#### Optional - Clerk Authentication:

```bash
VITE_ENABLE_CLERK_AUTH=true
VITE_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx
VITE_CLERK_SIGN_IN_URL=/sign-in
VITE_CLERK_SIGN_UP_URL=/sign-up
VITE_CLERK_AFTER_SIGN_IN_URL=/dashboard
VITE_CLERK_AFTER_SIGN_UP_URL=/dashboard
VITE_CLERK_FRONTEND_API_URL=https://your-clerk-frontend-api.clerk.accounts.dev
```

**How to Add Environment Variables in Vercel:**
1. Go to your project in Vercel Dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add each variable with its value
4. Select environments: **Production**, **Preview**, **Development**
5. Click **Save**

### 4. **Deploy**

1. Click **"Deploy"** in Vercel
2. Wait for the build to complete (~2-3 minutes)
3. Visit your deployment URL: `https://your-project.vercel.app`

---

## 🔄 Continuous Deployment

Once configured, Vercel automatically deploys:

- **Production**: Every push to `main` branch
- **Preview**: Every pull request
- **Development**: Every push to feature branches

---

## 🛠️ Configuration Files

### `vercel.json` (Root)
Configures the monorepo build, routing, and headers.

**Key Features:**
- ✅ Monorepo support (builds from `apps/dashboard`)
- ✅ SPA routing (all routes → `index.html`)
- ✅ Security headers (XSS, frame options, etc.)
- ✅ Asset caching (1 year for immutable assets)
- ✅ API proxy rewrites
- ✅ Node 22.x runtime

### `.vercelignore`
Excludes unnecessary files from deployment:
- Backend Python code
- Database files
- Documentation
- Test files
- Docker configurations

---

## 🌐 Domain Configuration

### Custom Domain Setup:

1. Go to **Settings** → **Domains** in Vercel
2. Click **"Add Domain"**
3. Enter your domain (e.g., `app.toolboxai.com`)
4. Follow DNS configuration instructions
5. Vercel automatically provisions SSL certificate

**DNS Records Required:**
```
Type: CNAME
Name: app (or @)
Value: cname.vercel-dns.com
```

---

## 🔒 Security Headers

Automatically configured in `vercel.json`:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS filtering |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer info |
| `Cache-Control` | `public, max-age=31536000, immutable` | Asset caching (1 year) |

---

## 🔗 API Proxy Configuration

The `vercel.json` includes rewrites for API calls:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "$VITE_API_BASE_URL/api/:path*"
    }
  ]
}
```

This allows the frontend to make API calls to `/api/*` which get proxied to your backend.

---

## 📊 Performance Optimization

### Configured Optimizations:

1. **Asset Caching**: 1-year cache for static assets
2. **Code Splitting**: Vite automatically splits code
3. **Tree Shaking**: Unused code removed
4. **Minification**: Production builds are minified
5. **Compression**: Gzip/Brotli enabled by default
6. **Edge Network**: Served from Vercel's global CDN

### Bundle Size:

Expected production bundle sizes:
- **Vendor**: ~500-800 KB (React, Mantine, Three.js)
- **App**: ~200-400 KB (application code)
- **Total**: ~700-1200 KB (gzipped: ~250-400 KB)

---

## 🐛 Troubleshooting

### Build Fails

**Issue**: "Module not found" errors
**Solution**:
```bash
# Ensure all dependencies are in package.json
cd apps/dashboard
npm install
npm run build  # Test locally first
```

**Issue**: "Out of memory" during build
**Solution**: Upgrade Vercel plan or optimize build:
```json
// In package.json, increase Node memory
"build": "NODE_OPTIONS=--max-old-space-size=4096 vite build"
```

### Runtime Errors

**Issue**: API calls fail (CORS errors)
**Solution**:
1. Ensure `VITE_API_BASE_URL` is set correctly
2. Backend must allow requests from Vercel domain
3. Check backend CORS configuration

**Issue**: Environment variables not working
**Solution**:
1. Variables must be prefixed with `VITE_`
2. Redeploy after adding environment variables
3. Clear browser cache

### Routing Issues

**Issue**: 404 on page refresh
**Solution**: Already configured in `vercel.json`:
```json
{
  "routes": [
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

---

## 📈 Monitoring & Analytics

### Vercel Analytics (Built-in)

1. Go to **Analytics** tab in Vercel Dashboard
2. View:
   - Page views
   - Unique visitors
   - Top pages
   - Load times
   - Core Web Vitals

### Custom Monitoring

Add monitoring tools via environment variables:
```bash
# Sentry (Error Tracking)
VITE_SENTRY_DSN=your-sentry-dsn

# Google Analytics
VITE_GA_TRACKING_ID=G-XXXXXXXXXX

# PostHog (Product Analytics)
VITE_POSTHOG_KEY=your-posthog-key
```

---

## 🔄 Rollback Strategy

If a deployment fails:

1. **Instant Rollback**:
   - Go to **Deployments** tab
   - Find previous successful deployment
   - Click **...** → **Promote to Production**

2. **Revert Git Commit**:
   ```bash
   git revert HEAD
   git push origin main
   # Vercel auto-deploys the reverted version
   ```

---

## 💰 Cost Considerations

### Free Tier Includes:
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth per month
- ✅ 100 GB-hours compute per month
- ✅ Automatic SSL certificates
- ✅ Global CDN
- ✅ Preview deployments

### Pro Tier ($20/month):
- 1 TB bandwidth
- 1000 GB-hours compute
- Team collaboration
- Password protection
- Advanced analytics

---

## 📚 Additional Resources

- **Vercel Documentation**: https://vercel.com/docs
- **Vite Documentation**: https://vitejs.dev/guide
- **React 19 Documentation**: https://react.dev
- **Mantine UI Documentation**: https://mantine.dev

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] Backend API is deployed and accessible
- [ ] All environment variables are configured
- [ ] Pusher credentials are set (if using realtime features)
- [ ] Custom domain is configured (optional)
- [ ] SSL certificate is active
- [ ] Build succeeds locally (`npm run build`)
- [ ] No console errors in browser
- [ ] API calls work correctly
- [ ] Authentication works (if enabled)
- [ ] Monitoring is configured

---

## 🎉 Success!

Your ToolboxAI Solutions dashboard is now deployed on Vercel with:
- ⚡ Lightning-fast global CDN
- 🔒 Enterprise-grade security headers
- 🔄 Automatic CI/CD from GitHub
- 📊 Built-in analytics
- 🌐 Custom domain support
- 🔐 Automatic SSL certificates

**Production URL**: `https://your-project.vercel.app`

---

## 💡 Tips

1. **Use Preview Deployments**: Test changes in preview before merging to main
2. **Enable Branch Deployments**: Every branch gets a unique URL
3. **Configure Alerts**: Get notified of deployment failures
4. **Use Vercel CLI**: Deploy from command line with `vercel` command
5. **Monitor Performance**: Use Vercel Analytics to track Core Web Vitals

---

**Need Help?**
- Vercel Support: https://vercel.com/support
- GitHub Issues: https://github.com/GrayGhostDev/ToolboxAI-Solutions/issues
- Documentation: This file + `CLAUDE.md`

**Last Updated**: October 20, 2025
