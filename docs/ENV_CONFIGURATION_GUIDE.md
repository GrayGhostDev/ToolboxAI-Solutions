# Environment Configuration Guide

**Last Updated:** 2025-11-07
**Status:** Production-Ready

---

## 📁 File Structure Overview

### Environment Files (After Cleanup)

```
Root Directory:
├── .env                    # ✅ PROTECTED - Your actual credentials (gitignored)
├── .env.example            # ✅ TRACKED - Template with placeholders only
├── .env.local.example      # ✅ TRACKED - Local override template
└── .env.production         # ✅ PROTECTED - Production template (gitignored)

apps/dashboard/:
├── .env.local              # ✅ PROTECTED - Frontend local dev (gitignored)
└── .env.example            # ✅ TRACKED - Frontend template

apps/backend/:
└── .env.example            # ✅ TRACKED - Backend template

config/env-templates/:
├── production.env.example  # ✅ TRACKED - Production template
├── staging.env.example     # ✅ TRACKED - Staging template
└── database.env.example    # ✅ TRACKED - Database template

infrastructure/render/:
└── ENVIRONMENT_VARIABLES.template  # ✅ TRACKED - Render deployment template
```

---

## 🔒 Security Model

### Protected Files (Never Committed to Git)

These files are automatically ignored by `.gitignore`:
- `.env` - Your actual production/development credentials
- `.env.local` - Machine-specific overrides
- `.env.production` - Production secrets
- `.env.development` - Development secrets
- `.env.staging` - Staging secrets
- `.env.*.local` - Any local variant
- `.env.secret` - Secret storage

**⚠️ CRITICAL:** These files should NEVER be committed to version control.

### Template Files (Safe to Commit)

These files contain ONLY placeholders and are safe to track:
- `.env.example` - All template files ending in `.example`
- They use placeholders like `your_api_key_here` or `[REQUIRED]`
- No real credentials should ever be in these files

---

## 🚀 Getting Started

### For New Developers

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ToolBoxAI-Solutions
   ```

2. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

3. **Fill in your credentials:**
   ```bash
   # Open .env and replace all placeholder values with real credentials
   nano .env  # or your preferred editor
   ```

4. **Get credentials from:**
   - **Supabase:** https://supabase.com/dashboard → Your Project → Settings → API
   - **OpenAI:** https://platform.openai.com/api-keys
   - **Anthropic:** https://console.anthropic.com/settings/keys
   - **Clerk:** https://dashboard.clerk.com → Your App → API Keys
   - **Pusher:** https://dashboard.pusher.com → Your App → App Keys
   - (See `.env.example` for complete list)

5. **Verify your setup:**
   ```bash
   # Backend
   cd apps/backend
   python -c "from dotenv import load_dotenv; load_dotenv('../../.env'); print('✅ Environment loaded')"

   # Frontend
   cd apps/dashboard
   npm run dev  # Should load VITE_ variables from root .env
   ```

---

## 📝 Environment Variable Categories

### 1. Supabase Integration

```bash
# Core Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_public_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
SUPABASE_DATABASE_URL=postgresql://postgres:your_password@db.your-project-id.supabase.co:6543/postgres?sslmode=require
SUPABASE_STORAGE_BUCKET=your-bucket-name

# S3-Compatible Storage (Optional)
SUPABASE_S3_ENDPOINT=https://your-project-id.storage.supabase.co/storage/v1/s3
SUPABASE_S3_REGION=us-east-1
SUPABASE_S3_ACCESS_KEY_ID=your_s3_access_key_id
SUPABASE_S3_SECRET_ACCESS_KEY=your_s3_secret_access_key

# Frontend Variables (for Vite builds)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_public_key_here
```

**Where to get:** Supabase Dashboard → Project Settings → API & S3 Access Keys

### 2. AI Services

```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
REPLICATE_API_TOKEN=r8_...
```

**Security:** These keys provide access to paid services. Rotate immediately if exposed.

### 3. Authentication

```bash
CLERK_SECRET_KEY=sk_live_...
CLERK_PUBLISHABLE_KEY=pk_live_...
JWT_SECRET_KEY=<64-character-hex-string>
SESSION_SECRET=<64-character-hex-string>
```

**Generate secrets:**
```bash
openssl rand -hex 32  # For JWT_SECRET_KEY and SESSION_SECRET
```

### 4. Database & Cache

```bash
DATABASE_URL=postgresql://user:password@host:port/database
POSTGRES_PASSWORD=your_secure_password
REDIS_URL=redis://user:password@host:port/db
```

### 5. Real-Time Communication

```bash
PUSHER_APP_ID=2050003
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
PUSHER_CLUSTER=us2

VITE_PUSHER_KEY=your_pusher_key  # Same as PUSHER_KEY for frontend
VITE_PUSHER_CLUSTER=us2
```

### 6. Monitoring

```bash
SENTRY_DSN=https://...@o123456.ingest.sentry.io/...
VITE_SENTRY_DSN=https://...@o123456.ingest.sentry.io/...  # Frontend
```

---

## ⚙️ Configuration Best Practices

### 1. Never Hardcode Credentials

**❌ Bad:**
```python
database_url = "postgresql://user:password@localhost/db"
```

**✅ Good:**
```python
import os
database_url = os.getenv("DATABASE_URL")
```

### 2. Use Environment-Specific Files

- **Development:** `.env` (local machine)
- **Production:** Use secrets manager (Render Secrets, AWS Secrets Manager, etc.)
- **CI/CD:** GitHub Secrets, TeamCity environment variables

### 3. Validate Required Variables on Startup

**Backend example (`apps/backend/config.py`):**
```python
import os

required_vars = [
    "DATABASE_URL",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "JWT_SECRET_KEY",
]

for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")
```

### 4. Rotate Credentials Regularly

- **API Keys:** Quarterly or after team changes
- **Database Passwords:** Semi-annually
- **JWT Secrets:** After security incidents
- **Access Tokens:** According to service recommendations

### 5. Use .env.local for Machine-Specific Overrides

```bash
# .env (committed template - team settings)
DATABASE_URL=postgresql://postgres:password@localhost/app_db

# .env.local (gitignored - your personal override)
DATABASE_URL=postgresql://postgres:mypassword@192.168.1.100/app_db
```

---

## 🔍 Troubleshooting

### Variables Not Loading

**Problem:** Application can't find environment variables

**Solutions:**
1. **Check file location:**
   ```bash
   ls -la .env  # Should be in project root
   ```

2. **Check file format:**
   ```bash
   # ✅ Correct format
   KEY=value

   # ❌ Incorrect formats
   KEY = value  # No spaces around =
   KEY: value   # Wrong delimiter
   ```

3. **Check loading in code:**
   ```python
   # Python
   from dotenv import load_dotenv
   load_dotenv()  # Must be called before accessing os.getenv()
   ```

   ```javascript
   // Node.js
   require('dotenv').config()  // Must be at top of file
   ```

### Frontend Variables Not Working

**Problem:** `VITE_` variables undefined in React app

**Solution:**
1. Vite only loads variables starting with `VITE_`
2. Restart dev server after changing `.env`
3. Variables are embedded at **build time**, not runtime

```bash
# After changing .env, restart:
npm run dev
```

### Git Tracking Environment Files

**Problem:** `.env` file accidentally committed

**Solutions:**
1. **Remove from git (if not yet pushed):**
   ```bash
   git rm --cached .env
   git commit -m "Remove .env from tracking"
   ```

2. **If already pushed (SECURITY INCIDENT):**
   ```bash
   # Immediately rotate ALL credentials in that file
   # Then remove from history:
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch .env' \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (dangerous!)
   git push origin --force --all
   ```

3. **Verify protection:**
   ```bash
   git ls-files | grep "\.env"  # Should return nothing except .env.example
   ```

---

## 🛡️ Security Checklist

Before deploying or committing:

- [ ] All `.env` files (without `.example`) are in `.gitignore`
- [ ] No real credentials in any `.example` files
- [ ] All placeholders clearly marked (e.g., `your_api_key_here`)
- [ ] Sensitive files have restrictive permissions (`chmod 600 .env`)
- [ ] API keys restricted to necessary permissions only
- [ ] Database users have minimum required privileges
- [ ] All credentials rotated after any potential exposure
- [ ] Production secrets stored in secrets manager, not `.env` files

---

## 📚 Additional Resources

- **Project Documentation:** `docs/`
- **Deployment Guide:** `docs/RENDER_DEPLOYMENT_GUIDE.md`
- **Security Policy:** `SECURITY.md`
- **Supabase Integration:** `SUPABASE_INTEGRATION_COMPLETE.md`
- **Gitignore Reference:** `.gitignore` (lines 58-79)

---

## 🆘 Need Help?

1. **Missing credentials?** Ask team lead for access to password manager
2. **Service setup?** Check service-specific documentation in `docs/`
3. **Deployment issues?** See `DEPLOYMENT_CHECKLIST.md`
4. **Security concerns?** Review `SECURITY.md` and contact security team

---

**Remember:** Credentials are secrets. Treat them like passwords. Never share them in chat, email, or commit them to git.

**Pro Tip:** Use a password manager like 1Password or LastPass to securely share credentials with team members.
