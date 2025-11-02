# Vercel Configuration for ToolBoxAI Dashboard

## 🎯 Project Settings (Configure in Vercel Dashboard)

### General Settings
Navigate to: `https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings`

#### Framework Preset
```
Framework Preset: Vite
```
- Automatically detects Vite projects
- Sets optimal build settings
- Configures static file serving

#### Root Directory
```
Root Directory: . (leave empty or use dot)
```
⚠️ **CRITICAL**: Since you deployed from `apps/dashboard` directory, Vercel treats that as the root. Do NOT set a subdirectory here!

#### Node.js Version
```
Node.js Version: 22.x (Latest)
```
- Matches your local environment
- Defined in package.json engines
- Auto-updated to latest 22.x patch

### Build & Development Settings

#### Build Command
```bash
npm run build
```
- Override in vercel.json: ✓ (configured)
- Runs `vite build`
- Generates static assets to `dist/`

#### Output Directory
```
dist
```
- Relative to Root Directory
- Contains index.html and assets
- Full path: `apps/dashboard/dist`

#### Install Command
```bash
npm install --legacy-peer-deps
```
- Resolves peer dependency conflicts
- Works with workspace setup
- Prevents installation errors

#### Development Command
```bash
npm run dev
```
- For Vercel dev environment
- Runs `vite` (dev server on port 5179)

### Environment Variables

Configure in: Settings → Environment Variables

#### Production Variables
```env
# API Configuration
VITE_API_URL=https://toolboxai-backend.onrender.com
VITE_ENVIRONMENT=production
NODE_ENV=production

# Node Build Options
NODE_OPTIONS=--max_old_space_size=4096

# Pusher (if used)
VITE_PUSHER_APP_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=us2

# Supabase (if used)
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Sentry
VITE_SENTRY_DSN=your_sentry_dsn
VITE_SENTRY_ENVIRONMENT=production
```

## 📋 vercel.json Configuration

Current configuration in `apps/dashboard/vercel.json`:

```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "framework": "vite",
  "installCommand": "npm install --legacy-peer-deps",
  "ignoreCommand": "git diff --quiet HEAD^ HEAD ./",
  
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://toolboxai-backend.onrender.com/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  
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
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        }
      ]
    }
  ],
  
  "regions": ["iad1"],
  "cleanUrls": true,
  "trailingSlash": false
}
```

## 🔧 Critical Vercel Dashboard Settings

### 1. Root Directory Configuration

**Location**: Settings → General → Root Directory

```
Root Directory: . (leave empty OR use a single dot)
```

**Why**: You deployed from `apps/dashboard` locally, so Vercel already knows that's the root. Setting a subdirectory here will cause "Root Directory does not exist" error.

**How to Set**:
1. Go to Vercel Dashboard
2. Select project: `toolbox-production-final`
3. Settings → General
4. Scroll to "Root Directory"
5. **LEAVE IT EMPTY** or set to `.` (single dot)
6. If it shows `apps/dashboard`, REMOVE it
7. Click Save

### 2. Build & Development Settings

**Location**: Settings → General → Build & Development Settings

```
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
Install Command: npm install --legacy-peer-deps
Development Command: npm run dev
```

**Override with vercel.json**: ✅ Enabled (recommended)

### 3. Node.js Version

**Location**: Settings → General → Node.js Version

```
Node.js Version: 22.x
```

**Specified in**: `apps/dashboard/package.json`
```json
{
  "engines": {
    "node": ">=22",
    "npm": ">=10"
  }
}
```

### 4. Environment Variables

**Location**: Settings → Environment Variables

Add the following for **Production** environment:

| Key | Value | Environment |
|-----|-------|-------------|
| `VITE_API_URL` | `https://toolboxai-backend.onrender.com` | Production |
| `VITE_ENVIRONMENT` | `production` | Production |
| `NODE_ENV` | `production` | Production |
| `NODE_OPTIONS` | `--max_old_space_size=4096` | Production |

### 5. Git Configuration

**Location**: Settings → Git

```
Production Branch: main
Ignored Build Step: Git-based (configured in vercel.json)
```

## 🚀 Deployment Workflow

### Automatic Deployments

1. **Push to main branch** → Production deployment
2. **Push to other branches** → Preview deployment
3. **Pull request** → Preview deployment with comment

### Manual Deployment via CLI

```bash
# From apps/dashboard directory
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard

# Deploy to production
vercel --prod

# Deploy preview
vercel

# Force rebuild
vercel --prod --force
```

## 🔍 Troubleshooting Stuck Deployments

### Issue: Build Completes but Deployment Stuck

**Symptoms**:
- Build logs show "built in XXms"
- Status stays "● Building" for >10 minutes
- URL shows "Deployment is building" page

**Common Causes**:

1. **Missing Root Directory Setting**
   - Fix: Set Root Directory to `apps/dashboard` in Vercel dashboard

2. **Wrong Output Directory**
   - Check: `dist` folder exists after build
   - Verify: `index.html` is in `dist/`

3. **Workspace Path Issues**
   - Build succeeds but output is in wrong location
   - Vercel can't find the built files

4. **Missing index.html**
   - Vite build must generate `dist/index.html`
   - Check local build: `npm run build && ls -la dist/`

### Solution Steps

#### Step 1: Fix Root Directory in Vercel Dashboard

1. Go to https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings
2. General → Root Directory
3. **MUST be empty or `.` (a single dot)**
4. If it shows `apps/dashboard`, DELETE it or change to `.`
5. Save and redeploy

**Why**: You deployed from `apps/dashboard`, so that's already the root. Setting it again causes "does not exist" error.

#### Step 2: Check Local Build

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/apps/dashboard

# Clean build
rm -rf dist
npm run build

# Verify output
ls -la dist/
# Should show: index.html, assets/, etc.

# Check index.html exists
cat dist/index.html | head -5
```

#### Step 3: Force Redeploy

```bash
# Cancel stuck deployment (if needed)
# Then force new deployment
vercel --prod --force --yes
```

#### Step 4: Check Vercel Logs

```bash
# Get deployment URL
vercel ls --prod

# Check logs
vercel logs <deployment-url>
```

## 📊 Verification Checklist

After deployment completes:

- [ ] Visit production URL
- [ ] Verify no "Deployment is building" message
- [ ] Check homepage loads
- [ ] Test navigation
- [ ] Verify API calls work
- [ ] Check browser console for errors
- [ ] Test on mobile
- [ ] Verify HTTPS certificate
- [ ] Check Sentry for errors

## 🎯 Expected Deployment Times

| Phase | Duration | What's Happening |
|-------|----------|------------------|
| Queueing | 5-30s | Waiting for build server |
| Installing | 30-60s | npm install dependencies |
| Building | 45-60s | vite build (9926 modules) |
| Uploading | 10-30s | Upload to CDN |
| Propagating | 1-5min | Edge network distribution |
| **Total** | **2-7min** | End-to-end deployment |

## 🔗 Quick Links

### Vercel Dashboard
- **Project**: https://vercel.com/grayghostdevs-projects/toolbox-production-final
- **Settings**: https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings
- **Deployments**: https://vercel.com/grayghostdevs-projects/toolbox-production-final/deployments
- **Logs**: Available per deployment

### Production URLs
- **Primary**: https://toolbox-production-final-grayghostdevs-projects.vercel.app
- **Latest**: https://toolbox-production-final-[hash]-grayghostdevs-projects.vercel.app

### Backend
- **Render API**: https://toolboxai-backend.onrender.com
- **Health**: https://toolboxai-backend.onrender.com/health

## 🎉 Summary

### Critical Settings for Success

1. ✅ **Root Directory**: `.` (empty or dot - NOT a subdirectory)
2. ✅ **Framework**: Vite
3. ✅ **Node Version**: 22.x
4. ✅ **Output Directory**: `dist`
5. ✅ **Build Command**: `npm run build`
6. ✅ **Install Command**: `npm install --legacy-peer-deps`

### Why Root Directory Must Be Empty

When you ran `vercel` from the `apps/dashboard` directory:
```
ToolBoxAI-Solutions/
└── apps/
    └── dashboard/            ← You deployed from HERE
        ├── package.json
        ├── vercel.json
        ├── vite.config.js
        ├── src/
        └── dist/
```

Vercel links the project to THIS directory as the root. Setting Root Directory to `apps/dashboard` tells Vercel to look for `apps/dashboard/apps/dashboard` which doesn't exist!

**Error**: `The specified Root Directory "apps/dashboard" does not exist`

**Solution**: 
- ❌ Root Directory: `apps/dashboard` (WRONG - causes error)
- ✅ Root Directory: `.` or empty (CORRECT - uses current directory)

---

**Next Step**: Clear/set Root Directory to `.` in Vercel Dashboard, then redeploy!

