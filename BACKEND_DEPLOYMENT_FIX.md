# Backend Deployment Fix - Action Required

## 🎯 Current Issue

**Problem:** Backend at `https://toolboxai-backend.onrender.com/health` is timing out (30+ seconds)
**Impact:** Dashboard shows infinite loading spinner (fixed with bypass mode temporarily)
**Solution:** Deploy backend to Render with proper configuration

---

## ✅ What's Already Done

- ✅ Frontend deployed to Vercel successfully
- ✅ Icon loading errors fixed (proper chunk ordering)
- ✅ Health check utility added to prevent infinite loading
- ✅ Security keys generated (see below)
- ✅ Docker build completed successfully
- ✅ Bypass mode enabled temporarily for frontend testing

---

## 🔑 Generated Security Keys (READY TO USE)

```bash
# JWT Authentication
JWT_SECRET_KEY=d1842450fccdf9d6e0ee11c1b5b0d5d696ec7285a714ee6a783e7a0a17ee9979
JWT_REFRESH_SECRET_KEY=94102bae4fd0e5147771c67a7725d473f50629cafb50951f6db37ee5e0b8d959

# Application Secret
SECRET_KEY=b7d5a4f43a37de6fee61786a241366c2329252696857cc049a49d9f528221242
```

**⚠️ IMPORTANT:** These keys are cryptographically secure (256-bit). Use them as-is.

---

## 📋 Step-by-Step Deployment

### Step 1: Authenticate with Render CLI

```bash
# Login to Render
render login

# Verify authentication
render whoami
```

**If CLI login fails**, use Render Dashboard UI instead (see Alternative Method below).

---

### Step 2: Create Pusher Application

**Required for real-time features**

1. Go to https://dashboard.pusher.com/
2. Click "Create App" or use existing app
3. Configure:
   - **App Name:** toolboxai-production
   - **Cluster:** us2 (United States - Oregon)
   - **Enable client events:** ✅
4. Get credentials from **App Keys** tab:

```
PUSHER_APP_ID: _______________
PUSHER_KEY: _______________
PUSHER_SECRET: _______________
PUSHER_CLUSTER: us2
```

5. Configure **Auth Endpoint**:
   - Go to **App Settings** tab
   - **Authorization:** Enable
   - **Auth Endpoint:** `https://toolboxai-backend.onrender.com/pusher/auth`

---

### Step 3: Check Render Service Status

```bash
# List all services
render services list -o json

# Check if toolboxai-backend exists
render services list -o json | grep toolboxai-backend
```

**Expected outcomes:**
- **Service exists:** Proceed to Step 4
- **Service doesn't exist:** Create service (see Alternative Method)
- **Service exists but suspended:** It's on free tier and sleeping

---

### Step 4: Configure Environment Variables

#### Option A: Via Render CLI

```bash
# Set generated security keys
render env set JWT_SECRET_KEY=d1842450fccdf9d6e0ee11c1b5b0d5d696ec7285a714ee6a783e7a0a17ee9979 --service toolboxai-backend
render env set JWT_REFRESH_SECRET_KEY=94102bae4fd0e5147771c67a7725d473f50629cafb50951f6db37ee5e0b8d959 --service toolboxai-backend
render env set SECRET_KEY=b7d5a4f43a37de6fee61786a241366c2329252696857cc049a49d9f528221242 --service toolboxai-backend

# Set Pusher credentials (use values from Step 2)
render env set PUSHER_APP_ID=YOUR_APP_ID --service toolboxai-backend
render env set PUSHER_KEY=YOUR_KEY --service toolboxai-backend
render env set PUSHER_SECRET=YOUR_SECRET --service toolboxai-backend
render env set PUSHER_CLUSTER=us2 --service toolboxai-backend

# Set OpenAI API key (required for AI features)
render env set OPENAI_API_KEY=YOUR_OPENAI_KEY --service toolboxai-backend
```

#### Option B: Via Render Dashboard (if CLI fails)

1. Go to https://dashboard.render.com
2. Select **toolboxai-backend** service
3. Click **Environment** tab
4. Add each variable:

| Key | Value | Notes |
|-----|-------|-------|
| `JWT_SECRET_KEY` | `d1842450fccdf9d6e0ee11c1b5b0d5d696ec7285a714ee6a783e7a0a17ee9979` | Copy exact value |
| `JWT_REFRESH_SECRET_KEY` | `94102bae4fd0e5147771c67a7725d473f50629cafb50951f6db37ee5e0b8d959` | Copy exact value |
| `SECRET_KEY` | `b7d5a4f43a37de6fee61786a241366c2329252696857cc049a49d9f528221242` | Copy exact value |
| `PUSHER_APP_ID` | Your Pusher App ID | From Step 2 |
| `PUSHER_KEY` | Your Pusher Key | From Step 2 |
| `PUSHER_SECRET` | Your Pusher Secret | From Step 2 |
| `PUSHER_CLUSTER` | `us2` | Oregon cluster |
| `OPENAI_API_KEY` | Your OpenAI key | From OpenAI dashboard |

5. Click **Save Changes**

---

### Step 5: Deploy Backend

#### Option A: Manual Deploy via CLI

```bash
# Trigger new deployment
render deploy --service toolboxai-backend

# Monitor deployment progress
render logs toolboxai-backend --tail
```

#### Option B: Manual Deploy via Dashboard

1. Go to https://dashboard.render.com
2. Select **toolboxai-backend**
3. Click **Manual Deploy** > **Deploy latest commit**
4. Wait 3-5 minutes for deployment

#### Option C: Deploy from Blueprint (if service doesn't exist)

```bash
# Deploy entire infrastructure from render.yaml
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Create blueprint
render blueprint create
```

---

### Step 6: Verify Backend Deployment

```bash
# Wait for deployment to complete (3-5 minutes)
# Then test health endpoint

curl -I https://toolboxai-backend.onrender.com/health

# Expected response:
HTTP/2 200
content-type: application/json
...

# Get detailed health info
curl https://toolboxai-backend.onrender.com/health | jq .

# Expected JSON:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-01-15T..."
}
```

**If timeout persists:**
- Service may be on **Free tier** and sleeping (30-60s wake-up time)
- Make multiple requests to wake it up
- Check logs: `render logs toolboxai-backend --tail 100`

---

### Step 7: Update CORS Configuration

The backend needs to allow requests from your Vercel domain.

```bash
# Add Vercel URL to ALLOWED_ORIGINS
render env set ALLOWED_ORIGINS="https://toolboxai-dashboard.onrender.com,https://toolbox-production-final-i38crpr94-grayghostdevs-projects.vercel.app,https://toolboxai.vercel.app" --service toolboxai-backend

# Redeploy to apply changes
render deploy --service toolboxai-backend
```

**Or via Dashboard:**
1. Environment tab > Add variable
2. Key: `ALLOWED_ORIGINS`
3. Value: `https://toolboxai-dashboard.onrender.com,https://toolbox-production-final-i38crpr94-grayghostdevs-projects.vercel.app,https://toolboxai.vercel.app`
4. Save > Manual Deploy

---

### Step 8: Enable Authentication on Frontend

Once backend is healthy, remove bypass mode:

```bash
cd apps/dashboard

# Update vercel.json
cat > vercel.json << 'EOF'
{
  "buildCommand": "npm install --production=false && npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install --production=false",
  "framework": "vite",
  "env": {
    "VITE_API_URL": "https://toolboxai-backend.onrender.com",
    "VITE_ENVIRONMENT": "production",
    "NODE_ENV": "production",

    "VITE_BYPASS_AUTH": "false",
    "VITE_PUSHER_KEY": "YOUR_PUSHER_KEY",
    "VITE_PUSHER_CLUSTER": "us2",
    "VITE_PUSHER_ENABLED": "true",
    "VITE_ENABLE_CLERK_AUTH": "false",
    "VITE_DEBUG_MODE": "false"
  }
}
EOF

# Deploy to Vercel
vercel --prod
```

---

### Step 9: Test Full Authentication Flow

1. **Open frontend:** https://toolbox-production-final-i38crpr94-grayghostdevs-projects.vercel.app
2. **Verify no infinite spinner** (should show login page)
3. **Test login:**
   - Try logging in with valid credentials
   - Check browser console for errors
   - Verify JWT token in localStorage
4. **Test dashboard:**
   - Should redirect to dashboard after login
   - Verify real-time features work
5. **Test Pusher connection:**
   - Open browser console
   - Look for: `Pusher : State changed : connecting -> connected`

---

## 🔍 Verification Checklist

After completing all steps:

- [ ] Backend health endpoint returns 200 OK
- [ ] Backend `/health` response shows `"status": "healthy"`
- [ ] Database connection confirmed
- [ ] Redis connection confirmed
- [ ] Frontend loads without infinite spinner
- [ ] Login page displays correctly
- [ ] Authentication flow works
- [ ] Dashboard renders after login
- [ ] Pusher real-time connection established
- [ ] No CORS errors in browser console

---

## ⚠️ Common Issues & Fixes

### Issue 1: Backend Times Out (30+ seconds)

**Causes:**
- Service on free tier and sleeping
- Service not deployed yet
- Environment variables missing

**Fixes:**
```bash
# Check service status
render service get toolboxai-backend

# View recent logs
render logs toolboxai-backend --tail 100

# Trigger new deployment
render deploy --service toolboxai-backend
```

### Issue 2: CORS Errors

**Symptoms:**
```
Access to fetch at 'https://toolboxai-backend.onrender.com' from origin 'https://toolbox-production-final-...' has been blocked by CORS policy
```

**Fix:**
```bash
# Update ALLOWED_ORIGINS to include Vercel URL
render env set ALLOWED_ORIGINS="https://toolboxai-dashboard.onrender.com,https://toolbox-production-final-i38crpr94-grayghostdevs-projects.vercel.app" --service toolboxai-backend

# Redeploy
render deploy --service toolboxai-backend
```

### Issue 3: Database Connection Failed

**Symptoms:**
- Health endpoint returns `"database": "disconnected"`
- Logs show `could not connect to server`

**Fix:**
```bash
# Verify DATABASE_URL is set
render env list --service toolboxai-backend | grep DATABASE_URL

# If missing, check render.yaml - should be auto-populated from Supabase/Render Postgres
```

### Issue 4: Pusher Authentication Failed

**Symptoms:**
```
Pusher : Error : {"type":"WebSocketError","error":{"type":"PusherError","data":{"code":4009}}}
```

**Fix:**
1. Verify Pusher credentials are correct in Render
2. Check auth endpoint is configured in Pusher dashboard
3. Test auth endpoint manually:
```bash
curl -X POST https://toolboxai-backend.onrender.com/pusher/auth \
  -H "Content-Type: application/json" \
  -d '{"socket_id":"123.456","channel_name":"presence-user-123"}'
```

---

## 📞 Alternative Method (No CLI Required)

### Create Service via Render Dashboard

If CLI doesn't work, create service manually:

1. **Go to Render Dashboard:** https://dashboard.render.com
2. **New Web Service**
3. **Connect Repository:**
   - Select your GitHub repo
   - Branch: `main`
4. **Configure Service:**
   - **Name:** toolboxai-backend
   - **Region:** Oregon (US West)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:**
     ```
     pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
     ```
   - **Start Command:**
     ```
     cd apps/backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 8
     ```
5. **Add Environment Variables** (from Step 4)
6. **Create Web Service**

---

## 🎯 Expected Timeline

- **Step 1-2 (Auth + Pusher):** 5-10 minutes
- **Step 3-5 (Configure + Deploy):** 10-15 minutes
- **Step 6-7 (Verify + CORS):** 5 minutes
- **Step 8-9 (Frontend + Test):** 10 minutes

**Total Time:** ~30-40 minutes

---

## 📊 Success Criteria

When complete, you should have:

✅ Backend responding at `https://toolboxai-backend.onrender.com/health`
✅ Frontend loading without infinite spinner
✅ Login functionality working
✅ Dashboard rendering correctly
✅ Real-time features operational via Pusher
✅ No errors in browser console
✅ Full authentication flow functional

---

## 📝 Next Steps After Deployment

1. **Monitor for 24 hours:**
   - Check Render logs periodically
   - Monitor Sentry for errors (if configured)
   - Verify uptime

2. **Optimize Performance:**
   - Review database query performance
   - Enable Redis caching
   - Configure CDN if needed

3. **Security Hardening:**
   - Add rate limiting
   - Configure IP allowlist (if needed)
   - Enable HTTPS-only cookies

4. **Documentation:**
   - Update deployment docs with actual URLs
   - Document any custom configuration
   - Share credentials securely with team

---

**Created:** January 15, 2025
**Status:** READY TO EXECUTE
**Action Required:** Complete Steps 1-9 to deploy backend
