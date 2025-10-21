# Vercel Dashboard Configuration Guide

## Complete Frontend Setup for ToolboxAI Dashboard

**Backend Status**: ✅ Deployed on Render at `https://toolboxai-solutions.onrender.com`
**Frontend**: Configure on Vercel to connect to backend

---

## Option 1: Automated Configuration (Recommended)

### Using the Configuration Script

```bash
# Make the script executable
chmod +x vercel-env-config.sh

# Run the script
./vercel-env-config.sh
```

This will automatically configure all environment variables using the Vercel CLI.

---

## Option 2: Manual Configuration via Vercel Dashboard

### Step 1: Access Environment Variables

1. Go to: https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings/environment-variables
2. You'll add each variable below for **Production**, **Preview**, and **Development** environments

### Step 2: Add Backend Configuration

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_API_BASE_URL` | `https://toolboxai-solutions.onrender.com` | All |
| `VITE_WS_URL` | `wss://toolboxai-solutions.onrender.com` | All |

### Step 3: Add Clerk Authentication

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_CLERK_PUBLISHABLE_KEY` | `pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA` | All |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA` | All |
| `VITE_ENABLE_CLERK_AUTH` | `true` | All |
| `VITE_CLERK_SIGN_IN_URL` | `/sign-in` | All |
| `VITE_CLERK_SIGN_UP_URL` | `/sign-up` | All |
| `VITE_CLERK_AFTER_SIGN_IN_URL` | `/dashboard` | All |
| `VITE_CLERK_AFTER_SIGN_UP_URL` | `/dashboard` | All |

### Step 4: Add Supabase Database

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_SUPABASE_URL` | `https://jlesbkscprldariqcbvt.supabase.co` | All |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZXNia3NjcHJsZGFyaXFjYnZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg0MzYzNTYsImV4cCI6MjA3NDAxMjM1Nn0.NQnqmLIM7UOwRKwTnoHUJSl440d1NzPrj1xipC2du14` | All |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://jlesbkscprldariqcbvt.supabase.co` | All |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZXNia3NjcHJsZGFyaXFjYnZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg0MzYzNTYsImV4cCI6MjA3NDAxMjM1Nn0.NQnqmLIM7UOwRKwTnoHUJSl440d1NzPrj1xipC2du14` | All |

### Step 5: Add Pusher Real-time

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_PUSHER_KEY` | `73f059a21bb304c7d68c` | All |
| `VITE_PUSHER_CLUSTER` | `us2` | All |
| `VITE_PUSHER_AUTH_ENDPOINT` | `/pusher/auth` | All |
| `VITE_ENABLE_PUSHER` | `true` | All |

### Step 6: Add Feature Flags

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_ENABLE_ANALYTICS` | `true` | All |
| `VITE_ENABLE_DEBUG_MODE` | `false` | Production/Preview, `true` for Development |
| `VITE_ENABLE_WEBSOCKET` | `true` | All |

### Step 7: Add Stripe (Optional - for payments)

| Variable | Value | Environments |
|----------|-------|--------------|
| `VITE_STRIPE_PUBLISHABLE_KEY` | `pk_test_your_key` | All (update with real key) |

---

## Option 3: Using Vercel CLI (Quick Method)

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link to project
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
vercel link

# Add environment variables one by one
vercel env add VITE_API_BASE_URL production
# When prompted, enter: https://toolboxai-solutions.onrender.com

# Repeat for each variable above
```

---

## Post-Configuration Steps

### 1. Trigger New Deployment

After adding all environment variables, trigger a new deployment:

**Via Vercel Dashboard:**
- Go to: https://vercel.com/grayghostdevs-projects/toolbox-production-final
- Click "Deployments" → "Redeploy" → "Redeploy to Production"

**Via Git Push:**
```bash
git commit --allow-empty -m "chore: trigger Vercel redeploy with new env vars"
git push origin feat/supabase-backend-enhancement
```

**Via Vercel CLI:**
```bash
vercel --prod
```

### 2. Verify Deployment

Once deployed, test the application:

1. **Visit**: https://toolbox-production-final.vercel.app
2. **Expected behavior**:
   - ✅ Dashboard loads without errors
   - ✅ Clerk authentication works (sign in/sign up)
   - ✅ API calls reach backend at `https://toolboxai-solutions.onrender.com`
   - ✅ Real-time features work via Pusher

### 3. Check Browser Console

Open browser DevTools (F12) and verify:
- No CORS errors
- API calls going to correct backend URL
- Pusher connection established
- No authentication errors

### 4. Test API Connectivity

```bash
# From browser console
fetch('https://toolboxai-solutions.onrender.com/health')
  .then(r => r.json())
  .then(console.log)

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "database": "connected"
# }
```

---

## Environment-Specific Configuration

### Production
- Use live Clerk keys (`pk_live_...`)
- Enable analytics
- Disable debug mode
- Use production Supabase project

### Preview (Git branches)
- Can use test Clerk keys
- Enable debug for testing
- Can use staging Supabase

### Development (Local)
- Test keys
- Debug mode enabled
- Can use localhost backend for local dev

---

## Troubleshooting

### Issue: CORS Errors

**Symptom**: Browser console shows CORS policy errors

**Solution**: Verify backend CORS_ORIGINS includes Vercel domain
```bash
# On Render, ensure this environment variable is set:
CORS_ORIGINS=https://toolbox-production-final.vercel.app,https://toolbox-production-final-*.vercel.app
```

### Issue: Clerk Authentication Not Working

**Symptom**: Users can't sign in

**Solution**:
1. Verify Clerk publishable key is correct
2. Check Clerk dashboard has Vercel domain in allowed origins
3. Ensure both `VITE_CLERK_PUBLISHABLE_KEY` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` are set

### Issue: API Calls Failing

**Symptom**: 404 errors or network errors for API calls

**Solution**:
1. Verify `VITE_API_BASE_URL` is exactly: `https://toolboxai-solutions.onrender.com`
2. Check backend is running: Visit `https://toolboxai-solutions.onrender.com/health`
3. Ensure no trailing slash in API URL

### Issue: Pusher Not Connecting

**Symptom**: Real-time features don't work

**Solution**:
1. Verify `VITE_PUSHER_KEY` matches backend configuration
2. Check Pusher dashboard for connection attempts
3. Ensure `VITE_PUSHER_CLUSTER` is `us2`
4. Test Pusher auth endpoint: `https://toolboxai-solutions.onrender.com/pusher/auth`

---

## Security Notes

### Sensitive Variables

These variables are **SAFE** to expose in frontend:
- ✅ `VITE_CLERK_PUBLISHABLE_KEY` (public key)
- ✅ `VITE_SUPABASE_ANON_KEY` (read-only public key)
- ✅ `VITE_PUSHER_KEY` (public key)
- ✅ All `VITE_*` prefixed variables

These should **NEVER** be in frontend:
- ❌ `CLERK_SECRET_KEY` (backend only)
- ❌ `SUPABASE_SERVICE_ROLE_KEY` (backend only)
- ❌ `PUSHER_SECRET` (backend only)
- ❌ Database passwords
- ❌ Private API keys

### Environment Variable Visibility

Vercel environment variables marked for specific environments:
- **Production**: Used in production deployments
- **Preview**: Used for branch/PR deployments
- **Development**: Used for local `vercel dev`

---

## Complete Variable Checklist

Before deploying, ensure you have:

**Backend API** (2 variables)
- [ ] VITE_API_BASE_URL
- [ ] VITE_WS_URL

**Clerk Auth** (7 variables)
- [ ] VITE_CLERK_PUBLISHABLE_KEY
- [ ] NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
- [ ] VITE_ENABLE_CLERK_AUTH
- [ ] VITE_CLERK_SIGN_IN_URL
- [ ] VITE_CLERK_SIGN_UP_URL
- [ ] VITE_CLERK_AFTER_SIGN_IN_URL
- [ ] VITE_CLERK_AFTER_SIGN_UP_URL

**Supabase** (4 variables)
- [ ] VITE_SUPABASE_URL
- [ ] VITE_SUPABASE_ANON_KEY
- [ ] NEXT_PUBLIC_SUPABASE_URL
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY

**Pusher** (4 variables)
- [ ] VITE_PUSHER_KEY
- [ ] VITE_PUSHER_CLUSTER
- [ ] VITE_PUSHER_AUTH_ENDPOINT
- [ ] VITE_ENABLE_PUSHER

**Feature Flags** (3 variables)
- [ ] VITE_ENABLE_ANALYTICS
- [ ] VITE_ENABLE_DEBUG_MODE
- [ ] VITE_ENABLE_WEBSOCKET

**Total: 20 required variables**

---

## Quick Links

- **Vercel Dashboard**: https://vercel.com/grayghostdevs-projects/toolbox-production-final
- **Environment Variables**: https://vercel.com/grayghostdevs-projects/toolbox-production-final/settings/environment-variables
- **Deployments**: https://vercel.com/grayghostdevs-projects/toolbox-production-final/deployments
- **Backend Health**: https://toolboxai-solutions.onrender.com/health
- **Backend Dashboard**: https://dashboard.render.com/

---

**Last Updated**: October 21, 2025
**Backend URL**: https://toolboxai-solutions.onrender.com
**Frontend URL**: https://toolbox-production-final.vercel.app
