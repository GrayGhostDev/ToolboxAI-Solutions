# Security Policy

## Known Vulnerabilities & Accepted Risk

### esbuild Dev Server Vulnerability (GHSA-67mh-4wv8-2f99)

**Status:** ⚠️ Accepted Known Issue

**Affected Package:** `esbuild` <= 0.24.2 (bundled within vite > tsx)

**Severity:** Moderate (CVSS 5.3)

**Impact:** 
- **Development server only** - allows cross-origin reads of dev server responses
- Requires user interaction (clicking malicious link)
- **Does NOT affect production builds**
- Limited to development environments

**Root Cause:**
Vite 7.2.2 (latest) specifies `tsx@^4.8.1` as a peer dependency, which allows versions up to `tsx@4.19.2`. These tsx versions bundle esbuild <= 0.24.2. The tsx team hasn't released a version with patched esbuild to npm, and vite hasn't updated their peer dependency range.

**Current Mitigation:**
1. ✅ Upgraded to Vite 7.2.2 (latest)
2. ✅ Explicit esbuild@0.25.10 override in dependencies
3. ✅ Node version constraint set to >=22.x (supports v24.9.0)
4. ✅ `audit-level=moderate` configured in .npmrc to allow safe development

**Monitoring Strategy:**
- **Quarterly Dependency Audits:** Check npm for tsx/vite updates (See calendar reminders below)
- **Automated Alerts:** Enable GitHub Dependabot if using GitHub
- **CI Pipeline:** `npm outdated` runs with each build to detect updates
- **Manual Check:** `npm audit` reports vulnerabilities; moderate-level accepted per this policy

**Timeline for Resolution:**
- Monitor tsx releases for esbuild@0.25.0+ support
- When available, vite will update their peer dependency
- This will automatically resolve once upstream updates are released

## Dependency Update Calendar

Schedule quarterly checks on:
- **January 15**: Q1 security review
- **April 15**: Q2 security review  
- **July 15**: Q3 security review
- **October 15**: Q4 security review

Commands to run during quarterly reviews:
```bash
npm outdated                    # Check for available updates
npm audit                       # Full security audit
npm update --save-dev           # Apply safe updates
```

## Vulnerability Reporting

If you discover a security vulnerability, please email security@toolboxai.com instead of using the issue tracker.

## Version Constraints

- **Node:** >= 22.x (tested with v24.9.0)
- **npm:** >= 10
- **Vite:** ^7.0.0 (currently 7.2.2)

## CI/CD Implications

### npm audit in CI

The `.npmrc` configuration allows moderate vulnerabilities. CI pipelines should:
1. Run `npm audit` to detect vulnerabilities
2. Fail only on **high** and **critical** vulnerabilities
3. Allow moderate vulnerabilities per this documented policy

### Example GitHub Actions Configuration:
```yaml
- name: Security Audit
  run: npm audit --audit-level=moderate
```

## Related Issues

- [esbuild GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99)
- [tsx GitHub Issues](https://github.com/esbuild/esbuild/issues)
- [Vite GitHub Issues](https://github.com/vitejs/vite/issues)

## Last Updated

November 7, 2025

**Updated by:** Security Review  
**Status:** Active & Monitored
