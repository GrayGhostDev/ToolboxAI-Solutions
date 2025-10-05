# Security Hardening Agent Tasks

**Agent Role**: Security Specialist - Comprehensive security audit and hardening
**Worktree**: parallel-worktrees/security-hardening
**Branch**: feature/security-audit-2025
**Port**: 8023
**Priority**: CRITICAL

---

## 🎯 PRIMARY MISSION

Conduct comprehensive security audit of entire application, fix all vulnerabilities, and implement enterprise-grade security measures.

---

## Phase 1: Security Audit (CRITICAL)

### Task 1.1: Run Automated Security Scans
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/Toolbox014/ToolboxAI-Solutions

# Python security audit
bandit -r apps/backend/ -f json -o security-report-bandit.json
safety check --json > security-report-safety.json

# Node.js security audit
npm audit --audit-level=moderate --json > security-report-npm.json
npm -w apps/dashboard audit --audit-level=moderate --json >> security-report-npm.json

# Check for secrets
detect-secrets scan --all-files > security-report-secrets.json

# Generate summary
cat > SECURITY_AUDIT_SUMMARY.md << 'EOF'
# Security Audit Report - October 2, 2025

## Automated Scan Results

### Bandit (Python)
[Results from bandit scan]

### Safety (Python Dependencies)
[Results from safety check]

### npm audit (Node.js)
[Results from npm audit]

### Secret Detection
[Results from detect-secrets]

## Manual Review Required
- 459 security references in backend code
- 65 backend TODOs/FIXMEs
- 14 dashboard TODOs/FIXMEs

EOF
```

### Task 1.2: Audit 459 Security References
```bash
# Find all security-related code
grep -r "security\|vulnerability\|CVE\|password\|secret\|token" apps/backend --include="*.py" > security-references.txt

# Categorize by severity
mkdir -p security-audit/
grep -i "critical\|high" security-references.txt > security-audit/critical-high.txt
grep -i "medium" security-references.txt > security-audit/medium.txt
grep -i "low\|info" security-references.txt > security-audit/low-info.txt
```

---

## Phase 2: Fix Critical Vulnerabilities

### Task 2.1: Remove Hardcoded Secrets
```bash
# Verify Vault integration
python apps/backend/services/vault_manager.py check

# If secrets still hardcoded, migrate them
python scripts/vault/migrate_secrets.py --verify

# Verify no secrets in code
detect-secrets scan --all-files --baseline .secrets.baseline
```

### Task 2.2: Fix SQL Injection Vulnerabilities
```python
# Review all database queries for raw SQL
# Replace with parameterized queries using SQLAlchemy ORM

# Example fix:
# ❌ BAD: f"SELECT * FROM users WHERE email = '{email}'"
# ✅ GOOD: session.query(User).filter(User.email == email).first()

# Create PR with all SQL injection fixes
```

### Task 2.3: Fix XSS Vulnerabilities
```typescript
// Review all React components for unsafe HTML rendering
// Replace dangerouslySetInnerHTML with safe alternatives

// ❌ BAD: <div dangerouslySetInnerHTML={{__html: userInput}} />
// ✅ GOOD: <div>{userInput}</div> or use DOMPurify

// Create list of all files needing fixes
find apps/dashboard/src -name "*.tsx" -exec grep -l "dangerouslySetInnerHTML" {} \; > xss-fixes-needed.txt
```

### Task 2.4: Implement CSRF Protection
```python
# Verify CSRF middleware is active
# apps/backend/middleware/security_headers.py

# Add CSRF token to all forms
# Update all POST/PUT/DELETE endpoints to require CSRF token
```

---

## Phase 3: Security Headers & Configuration

### Task 3.1: Validate Security Headers
```bash
# Test security headers on running server
curl -I http://localhost:8009/api/v1/health | grep -E "X-Frame-Options|Content-Security-Policy|Strict-Transport-Security"

# Expected headers:
# - X-Frame-Options: DENY
# - X-Content-Type-Options: nosniff
# - X-XSS-Protection: 1; mode=block
# - Strict-Transport-Security: max-age=31536000
# - Content-Security-Policy: default-src 'self'
# - Referrer-Policy: strict-origin-when-cross-origin
```

### Task 3.2: Configure CORS Properly
```python
# Verify CORS configuration in apps/backend/core/security/cors.py
# Ensure only production domains are allowed
# No wildcard (*) in production
```

---

## Phase 4: Authentication & Authorization

### Task 4.1: Verify JWT Security
```python
# Check JWT configuration
# - Algorithm: RS256 (not HS256)
# - Key rotation enabled
# - Token expiry configured
# - Refresh token implemented

# Review apps/backend/core/auth/jwt_manager.py
```

### Task 4.2: Implement RBAC Completely
```bash
# Verify all endpoints have proper role checks
grep -r "@requires_permission\|@requires_role" apps/backend/api/ --include="*.py" | wc -l

# Expected: All 57 endpoint files should have role checks
```

---

## Phase 5: Data Protection

### Task 5.1: Verify PII Encryption
```python
# Test PII encryption service
python << 'EOF'
from apps.backend.core.security.pii_encryption import PIIEncryption

pii = PIIEncryption()

# Test encryption/decryption
email = "user@example.com"
encrypted = pii.encrypt_field(email, "email")
decrypted = pii.decrypt_field(encrypted, "email")

assert decrypted == email, "PII encryption broken!"
print("✅ PII encryption working")
EOF
```

### Task 5.2: Implement Input Validation
```python
# Add Pydantic validation to all API endpoints
# Verify all user inputs are validated

# Example:
# from pydantic import BaseModel, EmailStr, constr

# class UserCreate(BaseModel):
#     email: EmailStr
#     password: constr(min_length=12, max_length=128)
#     name: constr(min_length=1, max_length=100)
```

---

## Phase 6: Dependency Security

### Task 6.1: Update Vulnerable Dependencies
```bash
# Python dependencies
pip list --outdated
safety check --full-report

# Update critical vulnerabilities
pip install --upgrade [package]

# Node.js dependencies
npm audit fix
npm audit fix --force  # if needed for breaking changes

# Document all dependency updates
```

### Task 6.2: Pin Dependency Versions
```bash
# Freeze Python dependencies
pip freeze > requirements.txt

# Update package-lock.json
npm -w apps/dashboard install
```

---

## Phase 7: Security Documentation

### Task 7.1: Create SECURITY.md
```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities to security@toolboxai.com

**Do not** create public GitHub issues for security vulnerabilities.

## Security Features

- JWT RS256 authentication
- RBAC with 9 predefined roles
- PII encryption (AES-256-GCM)
- GDPR compliance
- HashiCorp Vault for secrets
- Security headers (HSTS, CSP, etc.)
- Rate limiting
- SQL injection prevention
- XSS protection
- CSRF protection

## Security Audits

- Last audit: October 2, 2025
- Next scheduled audit: January 2, 2026
```

### Task 7.2: Create Security Runbooks
```bash
mkdir -p docs/security/

# Create incident response playbook
cat > docs/security/INCIDENT_RESPONSE.md << 'EOF'
# Security Incident Response Playbook

## 1. Detection
- Monitor security alerts
- Review logs daily
- Check Sentry for errors

## 2. Containment
- Isolate affected systems
- Block malicious IPs
- Disable compromised accounts

## 3. Eradication
- Remove malware/backdoors
- Patch vulnerabilities
- Rotate credentials

## 4. Recovery
- Restore from backups
- Verify system integrity
- Monitor for re-infection

## 5. Post-Incident
- Document incident
- Update security measures
- Conduct lessons learned

EOF

# Create security checklist
cat > docs/security/DEPLOYMENT_SECURITY_CHECKLIST.md << 'EOF'
# Pre-Deployment Security Checklist

## Before Every Deployment

- [ ] All dependencies up to date
- [ ] Security audit passing
- [ ] No hardcoded secrets
- [ ] HTTPS configured
- [ ] Security headers enabled
- [ ] CORS properly configured
- [ ] Rate limiting active
- [ ] Backups verified
- [ ] Monitoring configured
- [ ] Incident response plan ready

EOF
```

---

## Phase 8: GitHub Security Issues

### Task 8.1: Create Security Issues
```bash
# Create GitHub issues for each vulnerability found
gh issue create --title "Security: [Description]" \
  --label "security,priority: critical" \
  --body "## Vulnerability Description

[Details]

## Impact

[Impact assessment]

## Remediation

[Fix instructions]

## References

- CWE-XXX
- OWASP Top 10
"
```

---

## 🎯 SUCCESS CRITERIA

- [ ] Bandit scan: 0 critical, 0 high vulnerabilities
- [ ] Safety check: 0 critical, 0 high vulnerabilities
- [ ] npm audit: 0 critical, 0 high vulnerabilities
- [ ] detect-secrets: 0 secrets found
- [ ] All 459 security references reviewed
- [ ] SECURITY.md created
- [ ] Security headers validated
- [ ] RBAC implemented on all endpoints
- [ ] PII encryption verified
- [ ] GitHub security issues created
- [ ] Security documentation complete

---

## 📊 DELIVERABLES

1. ✅ SECURITY_AUDIT_SUMMARY.md
2. ✅ SECURITY.md
3. ✅ docs/security/INCIDENT_RESPONSE.md
4. ✅ docs/security/DEPLOYMENT_SECURITY_CHECKLIST.md
5. ✅ All vulnerabilities fixed
6. ✅ All security issues documented in GitHub

---

**CRITICAL**: No deployment until all critical and high vulnerabilities are fixed!
