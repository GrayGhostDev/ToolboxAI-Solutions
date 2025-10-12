# ToolboxAI-Solutions - Production Deployment Checklist
## Complete Pre-Deployment Guide

**Date:** 2025-10-10
**Status:** Ready for Staging Deployment
**Issues Resolved:** 12 of 14 (85.7%)

---

## 📋 Pre-Deployment Summary

### Issues Resolved in This Session
- ✅ **Issues #17, #24-27, #33-35**: Documentation workflow (7 issues)
- ✅ **Issue #28**: Email service integration
- ✅ **Issue #29**: Stripe payment integration
- ✅ **Issue #30**: OAuth 2.1 token revocation (verified complete)
- ✅ **Issue #31**: User data encryption with Fernet
- ✅ **Issue #32**: Roblox environment database persistence
- ✅ **Issue #37**: Storage upload & media endpoints

### Remaining Issues (2)
- ⏳ **Issue #38**: Multi-tenancy middleware (backend complete, needs integration)
- ⏳ **Issue #39**: Pusher client integration (frontend hooks needed)

---

## 🔐 Environment Variables Configuration

### Required Environment Variables

#### Core Application
```bash
# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<generate_with_openssl_rand_hex_32>

# Database
DATABASE_URL=postgresql://user:password@host:5432/toolboxai_prod
REDIS_URL=redis://:password@host:6379/0

# JWT Authentication
JWT_SECRET_KEY=<generate_with_openssl_rand_hex_32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### Email Service (NEW - Issue #28)
```bash
# SendGrid Configuration
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SENDGRID_API_KEY=<your_sendgrid_api_key>
SMTP_USE_TLS=true

# Email Settings
FROM_EMAIL=noreply@toolboxai.com
FROM_NAME=ToolBoxAI
```

#### Stripe Payment (NEW - Issue #29)
```bash
# Stripe API
STRIPE_SECRET_KEY=sk_live_<your_live_key>
STRIPE_PUBLISHABLE_KEY=pk_live_<your_live_key>
STRIPE_WEBHOOK_SECRET=whsec_<your_webhook_secret>
ENABLE_STRIPE_WEBHOOKS=true
```

#### Data Encryption (NEW - Issue #31)
```bash
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
DATA_ENCRYPTION_KEY=<fernet_key_base64>

# Optional: Old keys for rotation
DATA_ENCRYPTION_KEY_OLD_1=<previous_key_1>
DATA_ENCRYPTION_KEY_OLD_2=<previous_key_2>

# Key rotation tracking
LAST_KEY_ROTATION=2025-10-10T00:00:00Z
```

#### File Storage
```bash
# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=<your_supabase_anon_key>
SUPABASE_SERVICE_KEY=<your_supabase_service_key>

# Virus Scanning
VIRUSTOTAL_API_KEY=<your_virustotal_key>  # Optional
ENABLE_VIRUS_SCANNING=true
```

#### Real-time (Pusher)
```bash
PUSHER_APP_ID=<your_app_id>
PUSHER_KEY=<your_key>
PUSHER_SECRET=<your_secret>
PUSHER_CLUSTER=<your_cluster>
VITE_PUSHER_KEY=<your_key>  # For frontend
VITE_PUSHER_CLUSTER=<your_cluster>
```

#### Vault Automation
```bash
# GitHub repository secrets required by vault-rotation workflow
VAULT_ADDR=https://vault.toolboxai.local:8200
VAULT_NAMESPACE=toolboxai
VAULT_ROLE_ID=<approle_role_id>
VAULT_SECRET_ID=<approle_secret_id>
```

> Ensure `.github/workflows/vault-rotation.yml` is enabled after deployment so nightly secret rotation runs uninterrupted.

---

## 🗄️ Database Migrations

### New Tables Added
1. **roblox_environments** - Stores Roblox environment configurations
2. **roblox_sessions** - Tracks play sessions
3. **environment_shares** - Manages environment sharing
4. **environment_templates** - Pre-built templates
5. **email_queue** - Email delivery queue (if using queue system)

### Run Migrations
```bash
# Navigate to project root
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions

# Activate virtual environment
source venv/bin/activate

# Generate migration for new models
alembic revision --autogenerate -m "Add Roblox environment models and email queue"

# Review the generated migration file
# Edit: alembic/versions/XXXX_add_roblox_environment_models.py

# Run migration
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\dt"
```

---

## 📦 Dependencies Check

### Python Dependencies (Already Installed)
```bash
# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0

# NEW: Encryption
cryptography>=41.0.0  # For Fernet encryption

# Email
jinja2>=3.1.0
sendgrid>=6.10.0  # Or your email provider

# Payments
stripe>=7.0.0

# Storage
supabase>=2.0.0

# Real-time
pusher>=3.3.0
```

### Install Missing Dependencies
```bash
pip install cryptography>=41.0.0
pip freeze > requirements.txt
```

---

## 🧪 Pre-Deployment Testing

### 1. Documentation Workflow Test
```bash
# Trigger documentation update
git add scripts/doc-updater/
git commit -m "test: trigger doc update workflow"
git push origin main

# Check GitHub Actions
# Expected: Workflow succeeds, no more failed issues created
```

### 2. Email Service Test
```python
# Test email sending
from apps.backend.workers.tasks.email_tasks import send_email

result = send_email.delay(
    to_email="test@example.com",
    subject="Test Email",
    template_name="notification",
    template_context={"title": "Test", "message": "Testing email service"}
)

# Check logs for success
# Check recipient inbox
```

### 3. Stripe Webhook Test
```bash
# Use Stripe CLI to test webhooks
stripe listen --forward-to localhost:8009/api/v1/stripe/webhooks

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.created

# Check database for created subscriptions
```

### 4. Encryption Test
```python
from apps.backend.core.security.encryption_manager import get_encryption_manager

manager = get_encryption_manager()

# Test encryption
encrypted = manager.encrypt("sensitive data")
decrypted = manager.decrypt(encrypted)

assert decrypted == "sensitive data"
print("✓ Encryption working")
```

### 5. File Upload Test
```bash
# Test multipart upload
curl -X POST http://localhost:8009/api/v1/uploads/multipart/init \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test-large-file.mp4",
    "file_size": 104857600,
    "mime_type": "video/mp4"
  }'

# Should return upload_id and part_count
```

### 6. Roblox Environment Test
```bash
# Create environment
curl -X POST http://localhost:8009/api/v1/roblox/environment/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Math World",
    "description": "A world for teaching geometry"
  }'

# List environments
curl http://localhost:8009/api/v1/roblox/environment/list \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return created environment from database
```

---

## 🚀 Deployment Steps

### 1. Code Deployment
```bash
# On production server

# Pull latest code
git pull origin main

# Activate virtualenv
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Collect static files (if applicable)
# npm run build (for dashboard)
```

### 2. Configure Stripe Webhooks
```bash
# In Stripe Dashboard:
# 1. Go to Developers > Webhooks
# 2. Add endpoint: https://your-domain.com/api/v1/stripe/webhooks
# 3. Select events:
#    - checkout.session.completed
#    - customer.subscription.created
#    - customer.subscription.updated
#    - customer.subscription.deleted
#    - invoice.payment_succeeded
#    - invoice.payment_failed
# 4. Copy webhook signing secret to STRIPE_WEBHOOK_SECRET
```

### 3. Configure SendGrid
```bash
# In SendGrid Dashboard:
# 1. Create API key with "Mail Send" permissions
# 2. Add to SENDGRID_API_KEY
# 3. Verify sender email (FROM_EMAIL)
# 4. Set up email templates (optional)
```

### 4. Generate Encryption Key
```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to DATA_ENCRYPTION_KEY environment variable
# IMPORTANT: Store backup of key securely (key vault, secrets manager)
```

### 5. Configure File Storage
```bash
# Supabase Setup:
# 1. Create storage bucket: "user-uploads"
# 2. Set up RLS policies for tenant isolation
# 3. Configure CDN if needed
# 4. Add API keys to environment
```

### 6. Restart Services
```bash
# Restart application servers
sudo systemctl restart toolboxai-backend
sudo systemctl restart toolboxai-dashboard

# Restart worker services
sudo systemctl restart toolboxai-celery-worker
sudo systemctl restart toolboxai-celery-beat

# Verify services running
sudo systemctl status toolboxai-*
```

---

## ✅ Post-Deployment Verification

### 1. Health Checks
```bash
# Backend API
curl https://your-domain.com/api/health
# Expected: {"status": "healthy"}

# Dashboard
curl https://your-domain.com/
# Expected: HTTP 200

# Database connection
curl https://your-domain.com/api/v1/health/db
# Expected: {"database": "connected"}
```

### 2. Feature Verification
- [ ] Send test email notification
- [ ] Process test Stripe payment
- [ ] Upload test file (both small and large)
- [ ] Create test Roblox environment
- [ ] Verify environment persisted in database
- [ ] Test OAuth token revocation
- [ ] Verify encryption/decryption works

### 3. Monitoring Setup
```bash
# Set up monitoring for:
- Email delivery rates (SendGrid dashboard)
- Payment success rates (Stripe dashboard)
- File upload success rates
- Database query performance
- Error rates in logs

# Configure alerts for:
- Failed email sends (>5% failure rate)
- Failed payments
- High storage usage
- Database connection issues
- Encryption key errors
```

---

## 🔧 Rollback Plan

### If Deployment Fails

#### 1. Database Rollback
```bash
# Rollback to previous migration
alembic downgrade -1

# Verify current version
alembic current
```

#### 2. Code Rollback
```bash
# Revert to previous release
git checkout <previous-release-tag>

# Restart services
sudo systemctl restart toolboxai-*
```

#### 3. Environment Variables
```bash
# Restore previous environment configuration
cp .env.backup .env

# Restart to reload env vars
sudo systemctl restart toolboxai-backend
```

---

## 📊 Monitoring & Alerts

### Key Metrics to Monitor

#### Email Service
- Delivery rate (target: >95%)
- Bounce rate (target: <2%)
- Queue depth (alert if >1000)
- Send failures (alert if >10/hour)

#### Payment Processing
- Successful payments (track revenue)
- Failed payments (alert immediately)
- Subscription churn rate
- Webhook processing time (target: <500ms)

#### File Storage
- Upload success rate (target: >98%)
- Virus scan hit rate
- Storage usage (alert at 80% capacity)
- CDN hit rate (target: >90%)

#### Database
- Connection pool usage (alert at 80%)
- Query performance (p95 < 100ms)
- Replication lag (if applicable)
- Disk usage (alert at 75%)

---

## 🔒 Security Checklist

### Before Going Live
- [ ] All API keys in environment variables (not in code)
- [ ] HTTPS enabled on all endpoints
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Encryption keys backed up securely
- [ ] Database credentials rotated
- [ ] Stripe webhook signature verification enabled
- [ ] File upload virus scanning enabled
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled
- [ ] CSRF tokens implemented
- [ ] Security headers configured

### Regular Security Tasks
- [ ] Weekly: Review failed login attempts
- [ ] Monthly: Rotate encryption keys
- [ ] Monthly: Review access logs
- [ ] Quarterly: Security audit
- [ ] Quarterly: Dependency updates
- [ ] Annually: Penetration testing

---

## 📝 Documentation Updates

### Update Before Launch
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Email template documentation
- [ ] Payment integration guide
- [ ] File upload limits and formats
- [ ] Encryption key management guide
- [ ] Monitoring runbook
- [ ] Incident response procedures

---

## 🎯 Success Criteria

### Deployment Successful When:
1. ✅ All health checks pass
2. ✅ No errors in application logs (first 24 hours)
3. ✅ Email delivery rate >95%
4. ✅ Payment processing functional
5. ✅ File uploads working (small and large)
6. ✅ Database queries performing well (p95 <100ms)
7. ✅ No security vulnerabilities detected
8. ✅ Monitoring and alerts configured

### Production Metrics (Week 1 Targets)
- Uptime: >99.5%
- API response time (p95): <200ms
- Email delivery: >95%
- Error rate: <0.5%
- User satisfaction: No critical bugs reported

---

## 👥 Team Responsibilities

### DevOps
- Deploy code to production
- Run database migrations
- Configure environment variables
- Set up monitoring and alerts

### Backend Team
- Verify API endpoints functional
- Test payment integration
- Monitor email delivery
- Check database performance

### Frontend Team
- Deploy dashboard
- Test Pusher integration
- Verify file uploads from UI
- Check responsive design

### QA Team
- Run full regression tests
- Test payment flow end-to-end
- Verify email notifications
- Test file upload scenarios
- Security testing

---

## 📞 Support Contacts

### Critical Issues
- On-Call DevOps: [Contact Info]
- Backend Lead: [Contact Info]
- Database Admin: [Contact Info]

### Service Providers
- Stripe Support: https://support.stripe.com
- SendGrid Support: https://support.sendgrid.com
- Supabase Support: https://supabase.com/support

---

## 📅 Timeline

### Suggested Deployment Schedule

**Day 1 (Staging)**
- Deploy to staging environment
- Run all tests
- Performance testing
- Security scan

**Day 2-3 (Staging Validation)**
- Load testing
- Integration testing
- User acceptance testing
- Bug fixes if needed

**Day 4 (Production Deploy)**
- Morning: Database migrations
- Afternoon: Code deployment
- Evening: Smoke tests
- Monitor overnight

**Day 5 (Monitoring)**
- Monitor all metrics
- Address any issues
- Performance tuning
- User feedback collection

---

**Deployment Checklist Last Updated:** 2025-10-10
**Next Review:** Before production deployment
**Maintainer:** DevOps Team

---

*This checklist should be reviewed and updated before each major deployment.*
