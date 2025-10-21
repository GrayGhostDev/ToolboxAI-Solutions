# Services Setup Guide

## How to Get Credentials for All Services

This guide walks you through creating accounts and obtaining API keys for every service used in the ToolboxAI deployment.

---

## 🗄️ 1. Supabase Database Setup

### Create Supabase Project

1. **Sign Up / Login**
   - Go to: https://app.supabase.com/
   - Click "Sign in" or "Start your project"
   - Use GitHub, Google, or email to sign up

2. **Create New Project**
   - Click "New Project"
   - Fill in details:
     - **Organization:** Create new or select existing
     - **Name:** `toolboxai-production`
     - **Database Password:** Generate strong password (save this!)
     - **Region:** Choose closest to Oregon (US West) - select `West US (North California)`
     - **Pricing Plan:** Start with Free tier
   - Click "Create new project"
   - Wait 2-3 minutes for database provisioning

### Get Supabase Credentials

#### Step 1: Get API Keys

1. Navigate to: **Settings → API** (left sidebar)
2. Copy the following values:

```bash
# Project URL
https://xyzcompany.supabase.co

# anon/public key
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...

# service_role key (⚠️ Keep secret!)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS...
```

#### Step 2: Get Database Connection String

1. Navigate to: **Settings → Database** (left sidebar)
2. Scroll to "Connection String"
3. Select **URI** tab
4. Copy the connection string:

```bash
postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

5. Replace `[YOUR-PASSWORD]` with the database password you created

#### Step 3: Configure Database

1. Navigate to: **SQL Editor**
2. Run initial schema setup (if you have migration files):

```sql
-- Your initial schema here
-- Or use Alembic migrations after backend is deployed
```

3. Navigate to: **Authentication → Settings**
   - Enable email provider
   - Configure JWT expiry (default 3600s is fine)

4. Navigate to: **Database → Tables**
   - Verify tables are created
   - Enable Row Level Security (RLS) on sensitive tables

### Supabase Environment Variables Summary

```bash
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
DATABASE_URL=postgresql://postgres...
```

---

## 🔐 2. Clerk Authentication Setup

### Create Clerk Application

1. **Sign Up / Login**
   - Go to: https://dashboard.clerk.com/
   - Click "Sign up" or "Sign in"
   - Use GitHub, Google, or email

2. **Create Application**
   - Click "+ Create application"
   - Fill in details:
     - **Application name:** `ToolboxAI Production`
     - **Sign-in options:**
       - ✅ Email address
       - ✅ Google (recommended)
       - ✅ GitHub (optional)
     - ✅ **Create this as a production instance** (for production deploy)
   - Click "Create application"

### Configure Clerk

#### Step 1: Configure Allowed Origins

1. Navigate to: **Settings → Domains** (left sidebar)
2. Add production domains:
   - `https://toolbox-production-final.vercel.app`
   - `https://toolboxai-backend.onrender.com` (for backend auth)
3. Add for testing:
   - `http://localhost:5179` (frontend dev)
   - `http://localhost:8009` (backend dev)

#### Step 2: Get API Keys

1. Navigate to: **API Keys** (left sidebar)
2. Copy the following:

**For Production:**
```bash
# Publishable key (frontend)
pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Secret key (backend)
sk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**For Development/Testing:**
```bash
# Publishable key (frontend)
pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Secret key (backend)
sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Step 3: Configure Webhooks

1. Navigate to: **Webhooks** (left sidebar)
2. Click "+ Add Endpoint"
3. Fill in:
   - **Endpoint URL:** `https://toolboxai-backend.onrender.com/api/v1/auth/clerk/webhook`
   - **Subscribe to events:**
     - ✅ `user.created`
     - ✅ `user.updated`
     - ✅ `user.deleted`
   - Click "Create"
4. Copy **Signing Secret** (you'll need this for webhook verification)

#### Step 4: Customize User Profile

1. Navigate to: **User & Authentication → Email, Phone, Username**
2. Configure required fields:
   - **Email:** Required
   - **Username:** Optional
   - **First/Last Name:** Optional
3. Navigate to: **User & Authentication → Social Connections**
   - Enable Google OAuth
   - Enable GitHub OAuth (optional)

### Clerk Environment Variables Summary

**Backend (Render):**
```bash
CLERK_SECRET_KEY=sk_live_xxxx (or sk_test_xxxx for development)
CLERK_PUBLISHABLE_KEY=pk_live_xxxx (or pk_test_xxxx for development)
```

**Frontend (Vercel):**
```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_live_xxxx
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxx
VITE_ENABLE_CLERK_AUTH=true
```

---

## 📡 3. Pusher Channels Setup

### Create Pusher Account

1. **Sign Up / Login**
   - Go to: https://dashboard.pusher.com/
   - Click "Sign up" or "Log in"
   - Use GitHub, Google, or email

2. **Create Channels App**
   - Click "Create app" or "Channels apps" → "+ Create app"
   - Fill in:
     - **App name:** `ToolboxAI Production`
     - **Cluster:** `us2` (US East Coast) - closest to your deployment
     - **Tech stack:**
       - **Frontend:** Vanilla JS (or React)
       - **Backend:** Python
   - Click "Create app"

### Get Pusher Credentials

1. Navigate to: **App Keys** tab
2. Copy all four values:

```bash
# App ID
1234567

# Key (public - goes in frontend)
a1b2c3d4e5f6g7h8i9j0

# Secret (⚠️ Keep secret! - backend only)
k1l2m3n4o5p6q7r8s9t0

# Cluster
us2
```

### Configure Pusher

#### Step 1: Enable Client Events (Optional)

1. Navigate to: **Settings** tab
2. Scroll to "Client events"
3. ✅ Enable client events (if you want client-to-client messaging)

#### Step 2: Configure Authorized Connections

1. Navigate to: **Settings** tab
2. Under "Authorized connections":
   - Add your domains:
     - `https://toolbox-production-final.vercel.app`
     - `https://toolboxai-backend.onrender.com`

#### Step 3: Test Connection

1. Navigate to: **Debug console** tab
2. You'll see events in real-time once your app is deployed

### Pusher Environment Variables Summary

**Backend (Render):**
```bash
PUSHER_APP_ID=1234567
PUSHER_KEY=a1b2c3d4e5f6g7h8i9j0
PUSHER_SECRET=k1l2m3n4o5p6q7r8s9t0
PUSHER_CLUSTER=us2
```

**Frontend (Vercel):**
```bash
VITE_PUSHER_KEY=a1b2c3d4e5f6g7h8i9j0
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth
VITE_ENABLE_PUSHER=true
```

---

## 🤖 4. OpenAI API (Optional - AI Features)

### Create OpenAI Account

1. **Sign Up / Login**
   - Go to: https://platform.openai.com/
   - Click "Sign up" or "Log in"

2. **Add Payment Method**
   - Navigate to: **Settings → Billing**
   - Add credit card
   - Set usage limits (recommended: $10/month to start)

### Get API Key

1. Navigate to: **API keys**
2. Click "+ Create new secret key"
3. Name it: `ToolboxAI Production`
4. Copy the key (you won't see it again!):

```bash
sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Environment Variable

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
```

---

## 🧠 5. Anthropic Claude API (Optional - AI Features)

### Create Anthropic Account

1. **Sign Up**
   - Go to: https://www.anthropic.com/
   - Request API access
   - Or use: https://console.anthropic.com/

2. **Get API Key**
   - Navigate to: **API Keys**
   - Click "Create Key"
   - Name it: `ToolboxAI Production`
   - Copy key:

```bash
sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Environment Variable

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx
```

---

## 📧 6. SendGrid Email (Optional - Transactional Emails)

### Create SendGrid Account

1. **Sign Up**
   - Go to: https://signup.sendgrid.com/
   - Fill in details (free tier: 100 emails/day)

2. **Verify Sender Email**
   - Navigate to: **Settings → Sender Authentication**
   - Click "Verify a Single Sender"
   - Enter your email: `noreply@yourdomain.com`
   - Verify via email link

### Get API Key

1. Navigate to: **Settings → API Keys**
2. Click "Create API Key"
3. Fill in:
   - **Name:** `ToolboxAI Production`
   - **Permissions:** Full Access (or restrict to Mail Send only)
4. Click "Create & View"
5. Copy key (you won't see it again!):

```bash
SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Environment Variables

```bash
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

---

## 📊 7. Sentry Error Monitoring (Optional)

### Create Sentry Account

1. **Sign Up**
   - Go to: https://sentry.io/signup/
   - Use GitHub or email

2. **Create Project**
   - Click "Create Project"
   - Select platform: **Python** (for backend)
   - Project name: `toolboxai-backend`
   - Click "Create Project"

3. **Create Frontend Project**
   - Repeat for: **React**
   - Project name: `toolboxai-frontend`

### Get DSN

1. Navigate to: **Settings → Projects → [Your Project] → Client Keys (DSN)**
2. Copy the DSN:

```bash
https://xxxxxxxxxxxxxxxxxxxxxxxxxxxx@o123456.ingest.sentry.io/123456
```

### Environment Variables

**Backend:**
```bash
SENTRY_DSN=https://xxxx@o123456.ingest.sentry.io/123456
```

**Frontend:**
```bash
VITE_SENTRY_DSN=https://xxxx@o123456.ingest.sentry.io/789012
```

---

## 🔒 8. JWT Secret Generation

### Generate Secure Secret

Run this command locally:

```bash
openssl rand -hex 32
```

Output example:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### Environment Variable

```bash
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**⚠️ IMPORTANT:** Never commit this to git! Only add to Render environment variables.

---

## ✅ Complete Environment Variables Checklist

Use this checklist to ensure you have all required credentials:

### Render Backend

- [ ] SUPABASE_URL
- [ ] SUPABASE_ANON_KEY
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] DATABASE_URL
- [ ] CLERK_SECRET_KEY
- [ ] CLERK_PUBLISHABLE_KEY
- [ ] JWT_SECRET_KEY (generated)
- [ ] JWT_ALGORITHM
- [ ] JWT_ACCESS_TOKEN_EXPIRE_MINUTES
- [ ] PUSHER_APP_ID
- [ ] PUSHER_KEY
- [ ] PUSHER_SECRET
- [ ] PUSHER_CLUSTER
- [ ] CORS_ORIGINS
- [ ] ENVIRONMENT
- [ ] DEBUG
- [ ] PYTHONPATH
- [ ] PYTHON_VERSION

### Optional Backend Variables

- [ ] OPENAI_API_KEY
- [ ] ANTHROPIC_API_KEY
- [ ] SENDGRID_API_KEY
- [ ] SENDGRID_FROM_EMAIL
- [ ] SENTRY_DSN

### Vercel Frontend

- [ ] VITE_API_BASE_URL
- [ ] VITE_WS_URL
- [ ] VITE_CLERK_PUBLISHABLE_KEY
- [ ] NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
- [ ] VITE_ENABLE_CLERK_AUTH
- [ ] VITE_SUPABASE_URL
- [ ] VITE_SUPABASE_ANON_KEY
- [ ] NEXT_PUBLIC_SUPABASE_URL
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY
- [ ] VITE_PUSHER_KEY
- [ ] VITE_PUSHER_CLUSTER
- [ ] VITE_PUSHER_AUTH_ENDPOINT
- [ ] VITE_ENABLE_PUSHER

### Optional Frontend Variables

- [ ] VITE_ENABLE_ANALYTICS
- [ ] VITE_SENTRY_DSN

---

## 📝 Quick Setup Order

Follow this order for smooth setup:

1. **Supabase** → Get database ready first
2. **Clerk** → Set up authentication
3. **Pusher** → Configure real-time
4. **JWT** → Generate secret key
5. **Render** → Deploy backend with all variables
6. **Vercel** → Deploy frontend with backend URL
7. **Optional Services** → Add AI, email, monitoring as needed

---

## 🆘 Need Help?

### Service Support

- **Supabase:** https://supabase.com/support
- **Clerk:** https://clerk.com/support
- **Pusher:** https://support.pusher.com/
- **Render:** https://render.com/docs/support
- **Vercel:** https://vercel.com/support

### Documentation

- **Supabase Docs:** https://supabase.com/docs
- **Clerk Docs:** https://clerk.com/docs
- **Pusher Docs:** https://pusher.com/docs
- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs

---

**Last Updated:** October 21, 2025
**Version:** 1.0.0
**Comprehensive Guide:** All services required for ToolboxAI deployment
