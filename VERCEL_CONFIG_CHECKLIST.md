# Vercel Configuration Checklist

Complete checklist for configuring ToolboxAI Dashboard on Vercel with Supabase.

## 📋 Project Information

- **Project Name**: `toolbox-production-final`
- **Project ID**: `prj_0TmmPwrRrSKPPfQtO48uIM9hLiZz`
- **Framework**: Vite 6.0.1 + React 19.1.0
- **Database**: Supabase (PostgreSQL)

## ✅ Pre-Deployment Checklist

### 1. Vercel Account Setup
- [ ] Vercel account created at [vercel.com](https://vercel.com)
- [ ] Vercel CLI installed: `npm install -g vercel`
- [ ] Logged in to Vercel CLI: `vercel login`
- [ ] Project linked: `vercel link`

### 2. Supabase Setup
- [ ] Supabase project created
- [ ] Database tables created
- [ ] Row Level Security (RLS) policies configured
- [ ] API keys obtained from Supabase dashboard

### 3. Pusher Setup
- [ ] Pusher app created at [dashboard.pusher.com](https://dashboard.pusher.com)
- [ ] Pusher credentials obtained (App ID, Key, Secret, Cluster)
- [ ] Pusher app configured to allow Vercel domains

## 🔐 Environment Variables Configuration

### Step 1: Access Vercel Environment Variables

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select project: `toolbox-production-final`
3. Navigate to **Settings** → **Environment Variables**

### Step 2: Add Required Variables

#### Core Application Variables

| Variable | Value | Environment | Required |
|----------|-------|-------------|----------|
| `VITE_API_BASE_URL` | Your backend API URL | Production, Preview | ✅ Yes |
| `VITE_PUSHER_KEY` | From Pusher dashboard | Production, Preview | ✅ Yes |
| `VITE_PUSHER_CLUSTER` | `us2` (or your cluster) | Production, Preview | ✅ Yes |
| `VITE_ENABLE_PUSHER` | `true` | Production, Preview | ✅ Yes |

#### Supabase Frontend Variables (Vite)

| Variable | Value | Environment | Required |
|----------|-------|-------------|----------|
| `VITE_SUPABASE_URL` | From Supabase dashboard | Production, Preview | ✅ Yes |
| `VITE_SUPABASE_ANON_KEY` | From Supabase dashboard | Production, Preview | ✅ Yes |

#### Supabase Frontend Variables (Next.js compatible)

| Variable | Value | Environment | Required |
|----------|-------|-------------|----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Same as VITE_SUPABASE_URL | Production, Preview | ⚠️ Optional* |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Same as VITE_SUPABASE_ANON_KEY | Production, Preview | ⚠️ Optional* |

*Only needed if using Next.js components or SSR

#### Supabase Backend Variables

| Variable | Value | Environment | Required |
|----------|-------|-------------|----------|
| `SUPABASE_URL` | From Supabase dashboard | Production, Preview | ✅ Yes |
| `SUPABASE_ANON_KEY` | From Supabase dashboard | Production, Preview | ✅ Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | From Supabase dashboard (⚠️ Secret) | Production, Preview | ✅ Yes |
| `SUPABASE_JWT_SECRET` | From Supabase dashboard (⚠️ Secret) | Production, Preview | ✅ Yes |

#### PostgreSQL Connection Variables (from Supabase)

| Variable | Value | Environment | Required |
|----------|-------|-------------|----------|
| `POSTGRES_URL` | From Supabase → Settings → Database | Production, Preview | ✅ Yes |
| `POSTGRES_PRISMA_URL` | From Supabase → Settings → Database | Production, Preview | ⚠️ If using Prisma |
| `POSTGRES_URL_NON_POOLING` | From Supabase → Settings → Database | Production, Preview | ⚠️ If needed |
| `POSTGRES_USER` | From Supabase → Settings → Database | Production, Preview | ⚠️ If needed |
| `POSTGRES_HOST` | From Supabase → Settings → Database | Production, Preview | ⚠️ If needed |
| `POSTGRES_PASSWORD` | From Supabase → Settings → Database | Production, Preview | ⚠️ If needed |
| `POSTGRES_DATABASE` | From Supabase → Settings → Database | Production, Preview | ⚠️ If needed |

#### Optional Variables

| Variable | Value | Environment | Required |
|----------|-------|-------------|----------|
| `VITE_ENABLE_CLERK_AUTH` | `false` | Production, Preview | ❌ No |
| `VITE_CLERK_PUBLISHABLE_KEY` | From Clerk dashboard | Production, Preview | ❌ No |
| `VITE_ENABLE_ANALYTICS` | `true` | Production, Preview | ❌ No |
| `VITE_SENTRY_DSN` | From Sentry dashboard | Production, Preview | ❌ No |

### Step 3: Obtain Supabase Values

#### From Supabase Dashboard

1. Go to [app.supabase.com](https://app.supabase.com)
2. Select your project
3. Navigate to **Settings** → **API**

**API Settings:**
- `VITE_SUPABASE_URL` / `SUPABASE_URL`: Project URL
- `VITE_SUPABASE_ANON_KEY` / `SUPABASE_ANON_KEY`: `anon` `public` key
- `SUPABASE_SERVICE_ROLE_KEY`: `service_role` `secret` key (⚠️ Keep secret!)

4. Navigate to **Settings** → **Database**

**Connection String:**
- `POSTGRES_URL`: Connection string (with pooler)
- `POSTGRES_PRISMA_URL`: Connection string for Prisma
- `POSTGRES_URL_NON_POOLING`: Direct connection (without pooler)

**Connection Info:**
- `POSTGRES_HOST`: Database host
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DATABASE`: Database name

5. Navigate to **Settings** → **API** → **JWT Settings**

- `SUPABASE_JWT_SECRET`: JWT secret (⚠️ Keep secret!)

## 🚀 Deployment Steps

### Quick Deployment

```bash
# Navigate to project root
cd /path/to/ToolboxAI-Solutions

# Deploy using script
./scripts/deployment/deploy-vercel.sh --production
```

### Manual Deployment

```bash
# Production
vercel --prod

# Preview
vercel
```

## 🔍 Verification Steps

### 1. Check Build Status

After deployment, verify:
- [ ] Build completed successfully
- [ ] No build errors in Vercel dashboard
- [ ] Assets deployed to CDN

### 2. Test Application

Visit your deployment URL and test:
- [ ] Application loads without errors
- [ ] Supabase connection working (check browser console)
- [ ] Pusher connection established
- [ ] API calls successful
- [ ] Authentication working (if enabled)
- [ ] Database queries working

### 3. Check Browser Console

Open browser console and verify:
- [ ] No CORS errors
- [ ] No Supabase connection errors
- [ ] No missing environment variable warnings
- [ ] Pusher successfully connected

### 4. Test Database Connection

```javascript
// In browser console
console.log('Supabase URL:', import.meta.env.VITE_SUPABASE_URL)
console.log('Supabase Key:', import.meta.env.VITE_SUPABASE_ANON_KEY?.substring(0, 20) + '...')

// Test connection
const { createClient } = window.supabaseClient
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

const { data, error } = await supabase.from('your_table').select('*').limit(1)
console.log('Database test:', { data, error })
```

## ⚠️ Common Issues & Solutions

### Issue 1: Supabase Connection Failed

**Symptoms:**
- Console errors: "Invalid API key" or "Could not connect to Supabase"
- Database queries failing

**Solutions:**
1. Verify `VITE_SUPABASE_URL` is correct (should be `https://xxxxx.supabase.co`)
2. Verify `VITE_SUPABASE_ANON_KEY` matches Supabase dashboard
3. Check Supabase project is not paused
4. Rebuild deployment: `vercel --prod --force`

### Issue 2: CORS Errors

**Symptoms:**
- Console errors: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solutions:**
1. Add Vercel domain to Supabase allowed origins:
   - Supabase Dashboard → Authentication → URL Configuration
   - Add: `https://toolbox-production-final.vercel.app`
   - Add: `https://*.vercel.app` (for preview deployments)

### Issue 3: Environment Variables Not Loading

**Symptoms:**
- `undefined` when accessing environment variables
- Application behaving as if variables are not set

**Solutions:**
1. Ensure variables are prefixed with `VITE_` for frontend access
2. Redeploy after adding variables: `vercel --prod`
3. Clear Vercel build cache: In Vercel Dashboard → Deployments → Redeploy → Clear cache and redeploy

### Issue 4: Database Queries Failing

**Symptoms:**
- Queries return no data or errors
- Row Level Security (RLS) violations

**Solutions:**
1. Check RLS policies in Supabase
2. Verify user is authenticated if required
3. Test query directly in Supabase SQL editor
4. Check database table permissions

### Issue 5: Service Role Key Exposed

**⚠️ CRITICAL SECURITY ISSUE**

**If service role key is exposed:**
1. **Immediately rotate** the key in Supabase Dashboard → Settings → API
2. Update `SUPABASE_SERVICE_ROLE_KEY` in Vercel
3. Redeploy application
4. Review access logs for unauthorized access

## 📊 Monitoring & Analytics

### Enable Vercel Analytics

1. Go to Vercel Dashboard → Analytics
2. Enable Web Analytics
3. Monitor:
   - Page load times
   - Core Web Vitals
   - Error rates
   - User experience

### Supabase Monitoring

1. Go to Supabase Dashboard → Reports
2. Monitor:
   - Database usage
   - API requests
   - Storage usage
   - Active connections

## 🔄 Post-Deployment Tasks

- [ ] Test all critical user flows
- [ ] Verify database connections
- [ ] Check Pusher real-time features
- [ ] Test authentication (if enabled)
- [ ] Monitor error rates
- [ ] Set up custom domain (optional)
- [ ] Enable Vercel Analytics
- [ ] Configure GitHub auto-deployments
- [ ] Set up monitoring/alerting
- [ ] Document any custom configurations

## 📚 Quick Reference Links

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Vercel Project**: https://vercel.com/dashboard/toolbox-production-final
- **Supabase Dashboard**: https://app.supabase.com
- **Pusher Dashboard**: https://dashboard.pusher.com
- **GitHub Repository**: [Your GitHub URL]

## 🆘 Support Resources

- **Vercel Support**: support@vercel.com
- **Supabase Support**: https://supabase.com/support
- **Pusher Support**: https://support.pusher.com
- **Project Issues**: GitHub Issues

---

**Last Updated**: October 16, 2025
**Project**: toolbox-production-final
**Status**: ✅ Configuration Complete - Ready for Deployment
