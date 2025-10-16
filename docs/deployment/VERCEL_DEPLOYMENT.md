# Vercel Deployment Guide

Complete guide for deploying ToolboxAI Dashboard to Vercel.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Environment Variables](#environment-variables)
4. [Deployment Process](#deployment-process)
5. [Custom Domain Setup](#custom-domain-setup)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Prerequisites

### Required Accounts
- **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
- **GitHub Account**: For connecting repository
- **Backend API**: Deployed and accessible (FastAPI backend)
- **Pusher Account**: For real-time features ([pusher.com](https://pusher.com))

### Required Tools
- Node.js >= 22
- npm >= 10
- Git

## Project Setup

### 1. Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### 2. Connect Repository

#### Option A: Vercel Dashboard (Recommended)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import Project"
3. Connect your GitHub account
4. Select the `ToolboxAI-Solutions` repository
5. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: `.` (leave as root)
   - **Build Command**: `npm run dashboard:build`
   - **Output Directory**: `apps/dashboard/dist`
   - **Install Command**: `npm install`

#### Option B: Vercel CLI

```bash
# Navigate to project root
cd /path/to/ToolboxAI-Solutions

# Login to Vercel
vercel login

# Deploy
vercel
```

### 3. Project Configuration

The `vercel.json` file in the root directory contains all configuration:

```json
{
  "buildCommand": "npm run dashboard:build",
  "outputDirectory": "apps/dashboard/dist",
  "installCommand": "npm install"
}
```

## Environment Variables

### Step 1: Gather Required Values

Before deploying, collect the following information:

1. **Backend API URL**: Your deployed FastAPI backend URL
2. **Pusher Credentials**: From [dashboard.pusher.com](https://dashboard.pusher.com)
   - App ID
   - Key
   - Cluster
3. **Optional Services**:
   - Clerk keys (if using Clerk auth)
   - Supabase keys (if using Supabase)
   - Sentry DSN (if using error tracking)

### Step 2: Add to Vercel

#### Via Dashboard

1. Go to your project on Vercel
2. Navigate to **Settings** > **Environment Variables**
3. Add the following variables:

**Required Variables:**

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_API_BASE_URL` | `https://your-backend.com` | Production, Preview |
| `VITE_PUSHER_KEY` | Your Pusher key | Production, Preview |
| `VITE_PUSHER_CLUSTER` | Your Pusher cluster (e.g., `us2`) | Production, Preview |
| `VITE_ENABLE_PUSHER` | `true` | Production, Preview |

**Optional Variables:**

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_ENABLE_CLERK_AUTH` | `false` | Production, Preview |
| `VITE_CLERK_PUBLISHABLE_KEY` | Your Clerk key (if enabled) | Production, Preview |
| `VITE_SUPABASE_URL` | Your Supabase URL (if enabled) | Production, Preview |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anon key (if enabled) | Production, Preview |
| `VITE_ENABLE_ANALYTICS` | `true` | Production, Preview |
| `VITE_SENTRY_DSN` | Your Sentry DSN (if enabled) | Production, Preview |

#### Via CLI

```bash
# Add environment variable
vercel env add VITE_API_BASE_URL production

# Add to all environments
vercel env add VITE_PUSHER_KEY production preview development
```

### Step 3: Verify Environment

Create a `.env.production` file locally to test:

```bash
# Copy template
cp .env.vercel.example .env.production

# Edit with your values
nano .env.production

# Test build locally
npm run dashboard:build
```

## Deployment Process

### Automatic Deployments

Vercel automatically deploys on:
- **Production**: Pushes to `main` branch
- **Preview**: Pull requests and other branches

### Manual Deployment

#### Via Dashboard
1. Go to your project on Vercel
2. Navigate to **Deployments**
3. Click **Deploy** > **Redeploy**

#### Via CLI
```bash
# Production deployment
vercel --prod

# Preview deployment
vercel
```

### Build Process

The build process follows these steps:

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Build Dashboard**
   ```bash
   npm run dashboard:build
   ```

3. **Optimize Assets**
   - Code splitting and tree shaking
   - Asset compression
   - CSS minification
   - Image optimization

4. **Deploy to CDN**
   - Static assets uploaded to Vercel Edge Network
   - Automatic cache invalidation

### Build Time

Expected build times:
- **First deployment**: 3-5 minutes
- **Subsequent deployments**: 1-3 minutes (with cache)

## Custom Domain Setup

### 1. Add Domain to Vercel

1. Go to your project **Settings** > **Domains**
2. Click **Add Domain**
3. Enter your domain (e.g., `dashboard.toolboxai.com`)
4. Click **Add**

### 2. Configure DNS

Vercel will provide DNS records to add:

#### Option A: Vercel Nameservers (Recommended)
```
Type: NS
Host: @
Value: ns1.vercel-dns.com
Value: ns2.vercel-dns.com
```

#### Option B: CNAME Record
```
Type: CNAME
Host: dashboard (or @)
Value: cname.vercel-dns.com
```

#### Option C: A Record
```
Type: A
Host: @ (or dashboard)
Value: 76.76.21.21
```

### 3. SSL Certificate

Vercel automatically provisions SSL certificates:
- Free Let's Encrypt certificates
- Automatic renewal
- HTTPS enforced by default

## Backend API Configuration

### Update vercel.json Routes

Update the backend API URL in `vercel.json`:

```json
{
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://your-actual-backend.com/api/$1"
    }
  ]
}
```

### CORS Configuration

Ensure your backend API allows requests from Vercel:

```python
# apps/backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "https://your-custom-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Build Failures

#### Issue: "Module not found" errors

**Solution**: Check that all dependencies are in `package.json`:

```bash
# Reinstall dependencies
npm install

# Test build locally
npm run dashboard:build
```

#### Issue: Out of memory during build

**Solution**: Increase Node.js memory:

```json
// package.json
{
  "scripts": {
    "dashboard:build": "NODE_OPTIONS='--max-old-space-size=4096' vite build"
  }
}
```

### Runtime Errors

#### Issue: API calls failing (CORS)

**Solution**:
1. Verify backend CORS configuration
2. Check `VITE_API_BASE_URL` environment variable
3. Verify backend is accessible from Vercel's network

#### Issue: Pusher connection failing

**Solution**:
1. Verify Pusher credentials in environment variables
2. Check Pusher app settings allow connections from Vercel
3. Test Pusher connection: https://dashboard.pusher.com/apps/YOUR_APP_ID/debug_console

### Performance Issues

#### Issue: Slow initial load

**Solution**:
1. Enable Vercel's **Image Optimization**
2. Use **Edge Functions** for API routes
3. Review bundle size: `npm run build:analyze`

#### Issue: High bandwidth usage

**Solution**:
1. Enable Gzip/Brotli compression (automatic on Vercel)
2. Optimize images and assets
3. Use Vercel's CDN caching headers

## Best Practices

### 1. Environment Management

```bash
# Use different configs per environment
.env.production      # Production only
.env.preview         # Preview deployments
.env.development     # Local development
```

### 2. Branch Strategy

- `main` → Production deployment
- `develop` → Staging/Preview deployment
- Feature branches → Preview deployments

### 3. Preview Deployments

Enable preview deployments for:
- Testing new features
- Client demos
- QA testing

Configure in **Settings** > **Git**:
- ✅ Enable Automatic Preview Deployments
- ✅ Enable Comments on Pull Requests

### 4. Performance Monitoring

Enable Vercel Analytics:
1. Go to **Analytics** tab
2. Enable **Web Analytics**
3. Monitor:
   - Page load times
   - Core Web Vitals
   - User experience metrics

### 5. Security Headers

Vercel automatically adds security headers from `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }
  ]
}
```

### 6. Caching Strategy

Optimal cache configuration:

```json
{
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/(.*).html",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=0, must-revalidate"
        }
      ]
    }
  ]
}
```

### 7. Deployment Checklist

Before each production deployment:

- [ ] Run tests locally: `npm test`
- [ ] Build successfully: `npm run dashboard:build`
- [ ] Verify environment variables in Vercel
- [ ] Test backend API connectivity
- [ ] Check Pusher configuration
- [ ] Review recent commits
- [ ] Create deployment note/changelog
- [ ] Monitor deployment logs
- [ ] Test production URL after deployment
- [ ] Verify critical user flows

## Additional Resources

### Vercel Documentation
- [Vercel Docs](https://vercel.com/docs)
- [Build Configuration](https://vercel.com/docs/build-step)
- [Environment Variables](https://vercel.com/docs/environment-variables)
- [Custom Domains](https://vercel.com/docs/custom-domains)

### Project-Specific
- [Main README](../../README.md)
- [Environment Setup](../configuration/ENVIRONMENT_SETUP.md)
- [Backend API Documentation](../api/README.md)

### Support
- **Vercel Support**: support@vercel.com
- **Project Issues**: GitHub Issues
- **Community**: [Vercel Discord](https://vercel.com/discord)

## Quick Reference

### Common Commands

```bash
# Deploy to production
vercel --prod

# Deploy preview
vercel

# View logs
vercel logs

# List deployments
vercel ls

# Remove deployment
vercel rm <deployment-url>

# Set environment variable
vercel env add VARIABLE_NAME production

# Pull environment variables
vercel env pull
```

### Deployment URLs

- **Production**: `https://your-project.vercel.app`
- **Custom Domain**: `https://your-custom-domain.com`
- **Preview**: `https://your-project-<hash>.vercel.app`

---

**Last Updated**: October 16, 2025
**Vercel CLI Version**: Latest
**Node Version**: 22
**Build Tool**: Vite 6.0.1
