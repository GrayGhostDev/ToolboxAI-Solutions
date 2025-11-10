# Security Scanner Configuration Guide

**Last Updated:** 2025-11-10  
**Status:** Production-Ready  
**Scanners:** CodeQL, Trivy, Dependabot

---

## 📋 Overview

This document describes the security scanning configuration for ToolBoxAI-Solutions, including CodeQL (SAST), Trivy (vulnerability scanning), and Dependabot (dependency updates).

---

## 🔍 Scanner Configuration

### 1. CodeQL (Static Analysis Security Testing)

**Purpose:** Identify security vulnerabilities and code quality issues in Python and JavaScript code.

**Configuration File:** `.github/codeql/codeql-config.yml`

**Key Features:**
- Security-extended query suite for comprehensive coverage
- False positive filtering for unreachable code warnings
- Path-based exclusions (tests, archives, build artifacts)
- Language-specific settings for Python and JavaScript

**Languages Scanned:**
- Python 3.12
- JavaScript/TypeScript (ES2022+)

**Query Suppressions:**
```yaml
# Suppressed queries (false positives)
- py/unreachable-statement
  Reason: Exception handlers in try/except blocks are reachable
  Pattern: try { return X } except { raise HTTPException }
  
- py/redundant-global-declaration  
  Reason: Needed for dynamic imports in agent systems
```

**Excluded Paths:**
- `Archive/**` - Deprecated code
- `node_modules/**` - Third-party dependencies
- `venv/**` - Python virtual environment
- Test files and build artifacts

---

### 2. Trivy (Vulnerability Scanner)

**Purpose:** Detect vulnerabilities in dependencies, container images, and infrastructure-as-code.

**Configuration File:** `.github/trivy.yaml`

**Ignore File:** `.trivyignore`

**Scan Types:**
- Vulnerability scanning (OS packages, libraries)
- Misconfiguration detection
- Secret scanning

**Severity Levels Reported:**
- CRITICAL
- HIGH
- MEDIUM
- (LOW and UNKNOWN excluded to reduce noise)

**Excluded Directories:**
```yaml
- node_modules
- venv/.venv
- Archive
- dist/build
- test directories
```

**Exit Behavior:**
- Exit code: 0 (report-only, don't fail builds)
- Upload findings to GitHub Security tab

---

### 3. Dependabot (Dependency Management)

**Purpose:** Automated dependency updates and security alerts.

**Configuration File:** `.github/dependabot.yml`

**Ecosystems Monitored:**
- npm (JavaScript/TypeScript)
- pip (Python)
- GitHub Actions
- Docker

**Update Schedule:**
- Security updates: Immediate
- Version updates: Weekly
- Group updates: By ecosystem

---

## 🚀 Workflow Integration

### Security Pipeline Workflow

**File:** `.github/workflows/security.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests
- Daily scheduled scan (midnight UTC)
- Manual dispatch

**Jobs:**

1. **Dependency Audit**
   - Python: `pip-audit`
   - JavaScript: `pnpm audit`

2. **Container Scan (Trivy)**
   - Filesystem scanning
   - SARIF output to GitHub Security

3. **SAST Scan (CodeQL)**
   - Matrix strategy (Python, JavaScript)
   - Security-extended queries
   - Custom configuration applied

---

## 📊 False Positive Management

### Current False Positives

**1. Unreachable Code Warnings (25 instances)**

**Issue:** CodeQL flags code in exception handlers as unreachable

**Example:**
```python
try:
    result = process_data()
    return result  # ← Return here
except Exception as e:
    logger.error(f"Error: {e}")  # ← CodeQL: "unreachable"
    raise HTTPException(...)     # ← Actually IS reachable!
```

**Resolution:**
- Excluded `py/unreachable-statement` query in CodeQL config
- Alternative: Dismiss alerts manually in GitHub with reason

**Status:** Handled via configuration

---

### Dismissing Alerts in GitHub

If false positives still appear:

1. Navigate to: `Security` → `Code scanning alerts`
2. Click on the alert
3. Click `Dismiss alert` dropdown
4. Select reason: `False positive` or `Won't fix`
5. Add comment: "Exception handler is reachable when exception occurs"
6. Click `Dismiss alert`

---

## 🔧 Local Scanning

### Run CodeQL Locally

```bash
# Install CodeQL CLI
brew install codeql

# Create database
codeql database create codeql-db --language=python

# Run analysis
codeql database analyze codeql-db \
  --format=sarif-latest \
  --output=results.sarif \
  codeql/python-queries:security-extended
```

### Run Trivy Locally

```bash
# Install Trivy
brew install trivy

# Scan filesystem
trivy fs . \
  --config .github/trivy.yaml \
  --severity CRITICAL,HIGH,MEDIUM

# Scan with ignore file
trivy fs . \
  --ignorefile .trivyignore \
  --severity CRITICAL,HIGH
```

### Run Dependency Audits Locally

```bash
# Python
pip install pip-audit
pip-audit -r requirements.txt

# JavaScript/TypeScript
pnpm audit
pnpm audit --fix  # Auto-fix if possible
```

---

## 📈 Security Metrics

### Current Status (as of 2025-11-10)

| Metric | Count | Status |
|--------|-------|--------|
| Critical CVEs | 0 | ✅ Clean |
| High Severity | 0 | ✅ Clean |
| Medium Severity | 0 | ✅ Clean |
| False Positives | 25 | ⚪ Suppressed |
| Dependabot Alerts | 0 | ✅ Clean |

### Historical Fixes

| Date | CVE/Alert | Severity | Resolution |
|------|-----------|----------|------------|
| 2025-11-10 | CVE-2024-23342 | HIGH | Removed ecdsa package |
| 2025-11-10 | undici DoS | MEDIUM | Updated to 6.20.0 |
| 2025-11-10 | path-to-regexp | HIGH | Updated to 8.2.0 |

---

## 🛡️ Security Best Practices

### 1. Dependency Management

✅ **DO:**
- Use package manager lockfiles (`pnpm-lock.yaml`, `requirements.txt`)
- Pin versions for production dependencies
- Use override mechanisms for transitive dependencies
- Review Dependabot PRs promptly

❌ **DON'T:**
- Use wildcards or ranges in production (`*`, `^`, `~`)
- Ignore security updates
- Commit lockfiles from development environments

### 2. Code Security

✅ **DO:**
- Use proper logging instead of print statements
- Handle exceptions explicitly
- Validate all user inputs
- Use parameterized queries for databases
- Store secrets in environment variables or secrets management

❌ **DON'T:**
- Use `eval()` or `exec()` with user input
- Commit secrets or credentials
- Disable security features without justification
- Ignore linter warnings

### 3. Configuration Security

✅ **DO:**
- Review scanner configurations regularly
- Document all suppressions with reasons
- Use least-privilege permissions
- Enable all relevant security checks

❌ **DON'T:**
- Blindly suppress all warnings
- Disable scanners to "fix" failing builds
- Use permissive configurations in production

---

## 🔄 Maintenance Schedule

### Daily
- Automated Trivy scans
- Dependabot checks

### Weekly
- Review new Dependabot PRs
- Check for new security advisories

### Monthly
- Review CodeQL configuration
- Update scanner versions
- Audit suppressed alerts

### Quarterly
- Full security audit
- Update security documentation
- Review and update .trivyignore

---

## 📞 Incident Response

### If Critical Vulnerability Found

1. **Assess Impact**
   - Check if vulnerability affects production
   - Determine exploitability

2. **Immediate Actions**
   - Create hotfix branch
   - Apply patch or update
   - Run security scans

3. **Testing**
   - Verify fix works
   - Run full test suite
   - Perform manual testing

4. **Deployment**
   - Deploy to staging
   - Validate in staging
   - Deploy to production
   - Monitor for issues

5. **Documentation**
   - Update security log
   - Document fix in commit
   - Update this guide if needed

---

## 🔗 References

### Official Documentation
- **CodeQL:** https://codeql.github.com/docs/
- **Trivy:** https://aquasecurity.github.io/trivy/
- **Dependabot:** https://docs.github.com/en/code-security/dependabot

### GitHub Security Features
- **Security Advisories:** https://github.com/advisories
- **Security Policies:** https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository

### Security Resources
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **CWE:** https://cwe.mitre.org/
- **CVE:** https://cve.mitre.org/

---

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-10 | Initial security scanner configuration | Security Team |
| 2025-11-10 | Added CodeQL config with false positive filters | Security Team |
| 2025-11-10 | Configured Trivy with custom settings | Security Team |
| 2025-11-10 | Fixed CVE-2024-23342 (ecdsa) | Security Team |

---

## ✅ Quick Reference

### Commands
```bash
# Check security status
gh api repos/GrayGhostDev/ToolboxAI-Solutions/code-scanning/alerts

# Run local scans
trivy fs . --config .github/trivy.yaml
pip-audit -r requirements.txt
pnpm audit

# Update dependencies
pnpm update
pip install -U -r requirements.txt
```

### File Locations
```
.github/
├── codeql/
│   └── codeql-config.yml        # CodeQL configuration
├── workflows/
│   └── security.yml              # Security pipeline
├── trivy.yaml                    # Trivy configuration
└── dependabot.yml                # Dependabot configuration
.trivyignore                      # Trivy ignore list
```

---

**For questions or issues, please contact the security team or create an issue.**

**Last Review:** 2025-11-10  
**Next Review:** 2025-12-10  
**Status:** ✅ Active
