# File Relocation Map

**Project Cleanup Date:** November 9, 2025
**Cleanup Scope:** Documentation reorganization, script organization, temporary file removal

## Purpose
This document maps all files that were relocated during the major cleanup to help team members find moved files and update any hardcoded references.

---

## Root Directory → /docs/11-reports/

| Old Location | New Location | Type |
|---|---|---|
| `/CODERABBIT_SETUP.md` | `/docs/11-reports/CODERABBIT_SETUP.md` | Status Report |
| `/DEPLOYMENT_STATUS.md` | `/docs/11-reports/DEPLOYMENT_STATUS.md` | Status Report |
| `/DOCUMENTATION_UPDATER_FIX_SUMMARY.md` | `/docs/11-reports/DOCUMENTATION_UPDATER_FIX_SUMMARY.md` | Status Report |
| `/NEXT_STEPS_RECOMMENDATIONS.md` | `/docs/11-reports/NEXT_STEPS_RECOMMENDATIONS.md` | Status Report |
| `/PNPM_MIGRATION_STATUS.md` | `/docs/11-reports/PNPM_MIGRATION_STATUS.md` | Status Report |
| `/PNPM_MIGRATION_STATUS_REPORT.md` | `/docs/11-reports/PNPM_MIGRATION_STATUS_REPORT.md` | Status Report |
| `/PNPM_MIGRATION_VERIFICATION.md` | `/docs/11-reports/PNPM_MIGRATION_VERIFICATION.md` | Status Report |
| `/TEAMCITY_STATUS_REPORT.md` | `/docs/11-reports/TEAMCITY_STATUS_REPORT.md` | Status Report |

---

## Root Security Docs → /docs/10-security/

| Old Location | New Location | Notes |
|---|---|---|
| `/SECURITY.md` | `/docs/10-security/ROOT_SECURITY.md` | Renamed to avoid conflicts |
| `/apps/dashboard/SECURITY.md` | `/docs/10-security/DASHBOARD_SECURITY.md` | Renamed to avoid conflicts |

---

## Dashboard App → /docs/06-features/dashboard/

| Old Location | New Location | Type |
|---|---|---|
| `/apps/dashboard/BROWSER_CONSOLE_FIXES.md` | `/docs/06-features/dashboard/BROWSER_CONSOLE_FIXES.md` | Troubleshooting |
| `/apps/dashboard/BUILD_SETUP_ANALYSIS.md` | `/docs/06-features/dashboard/BUILD_SETUP_ANALYSIS.md` | Build Guide |
| `/apps/dashboard/CHECKLIST.md` | `/docs/06-features/dashboard/CHECKLIST.md` | Task List |
| `/apps/dashboard/DOCUMENTATION_INDEX.md` | `/docs/06-features/dashboard/DOCUMENTATION_INDEX.md` | Index |
| `/apps/dashboard/FINAL_SUMMARY.md` | `/docs/06-features/dashboard/FINAL_SUMMARY.md` | Summary |
| `/apps/dashboard/IMPLEMENTATION_SUMMARY.md` | `/docs/06-features/dashboard/IMPLEMENTATION_SUMMARY.md` | Implementation |
| `/apps/dashboard/QUICK_REFERENCE.md` | `/docs/06-features/dashboard/QUICK_REFERENCE.md` | Reference |
| `/apps/dashboard/QUICK_START.md` | `/docs/06-features/dashboard/QUICK_START.md` | Getting Started |
| `/apps/dashboard/REDUX_PROVIDER_FIX.md` | `/docs/06-features/dashboard/REDUX_PROVIDER_FIX.md` | Fix Documentation |
| `/apps/dashboard/ROLE_AUTH_README.md` | `/docs/06-features/dashboard/ROLE_AUTH_README.md` | Feature Doc |
| `/apps/dashboard/ROLE_BASED_AUTH.md` | `/docs/06-features/dashboard/ROLE_BASED_AUTH.md` | Feature Doc |
| `/apps/dashboard/ROLE_ISSUE_RESOLVED.md` | `/docs/06-features/dashboard/ROLE_ISSUE_RESOLVED.md` | Resolution Doc |
| `/apps/dashboard/ROLE_SETUP_GUIDE.md` | `/docs/06-features/dashboard/ROLE_SETUP_GUIDE.md` | Setup Guide |
| `/apps/dashboard/TEST_NEW_COMPONENTS.md` | `/docs/06-features/dashboard/TEST_NEW_COMPONENTS.md` | Testing Guide |
| `/apps/dashboard/VISUAL_GUIDE.md` | `/docs/06-features/dashboard/VISUAL_GUIDE.md` | Visual Guide |

---

## Dashboard Images → /docs/images/

| Old Location | New Location | Type |
|---|---|---|
| `/apps/dashboard/login-page.png` | `/docs/images/login-page.png` | Screenshot |
| `/apps/dashboard/login-page-debug.png` | `/docs/images/login-page-debug.png` | Screenshot |

---

## Docker Compose Docs → /docs/08-operations/docker/

| Old Location | New Location | Type |
|---|---|---|
| `/infrastructure/docker/compose/KNOWN_ISSUES.md` | `/docs/08-operations/docker/KNOWN_ISSUES.md` | Issues List |
| `/infrastructure/docker/compose/SERVICE_STATUS.md` | `/docs/08-operations/docker/SERVICE_STATUS.md` | Status Report |
| `/infrastructure/docker/compose/SUPABASE_TEAMCITY_INTEGRATION.md` | `/docs/08-operations/docker/SUPABASE_TEAMCITY_INTEGRATION.md` | Integration Guide |
| `/infrastructure/docker/compose/TEAMCITY_RESTART_SUMMARY.md` | `/docs/08-operations/docker/TEAMCITY_RESTART_SUMMARY.md` | Operational Doc |
| `/infrastructure/docker/compose/TEAMCITY_UPGRADE_PROCEDURE.md` | `/docs/08-operations/docker/TEAMCITY_UPGRADE_PROCEDURE.md` | Procedure |

---

## PNPM Migration Docs → /docs/11-reports/migrations/

| Old Location | New Location | Type |
|---|---|---|
| `/docs/pnpm-migration-executive-summary.md` | `/docs/11-reports/migrations/pnpm-migration-executive-summary.md` | Migration Report |
| `/docs/pnpm-migration-implementation-plan.md` | `/docs/11-reports/migrations/pnpm-migration-implementation-plan.md` | Migration Plan |

---

## Root Scripts → /scripts/deployment/

| Old Location | New Location | Type |
|---|---|---|
| `/verify-system-health.sh` | `/scripts/deployment/verify-system-health.sh` | Health Check Script |
| `/check-dashboard-health.sh` | `/scripts/deployment/check-dashboard-health.sh` | Health Check Script |
| `/deploy-to-vercel.sh` | `/scripts/deployment/deploy-to-vercel.sh` | Deployment Script |
| `/DEPLOYMENT_VERIFICATION.sh` | `/scripts/deployment/DEPLOYMENT_VERIFICATION.sh` | Verification Script |
| `/apply-docker-fixes.sh` | `/scripts/deployment/apply-docker-fixes.sh` | Fix Script |
| `/DEPLOY_BACKEND_COMMANDS.sh` | `/scripts/deployment/DEPLOY_BACKEND_COMMANDS.sh` | Deployment Script |

---

## Test Files → /tests/diagnostics/

| Old Location | New Location | Type |
|---|---|---|
| `/test_router_import.py` | `/tests/diagnostics/test_router_import.py` | Diagnostic Test |

---

## Merged Directories

### `__tests__/` → `tests/`
The JavaScript-style `__tests__/` directory was merged into the Python-style `tests/` directory for consistency.

**Actions taken:**
- All files from `__tests__/` copied to `tests/`
- `__tests__/` directory removed
- Check `tests/` for all test files

---

## Files DELETED (Not Relocated)

### Placeholder Files (Root)
- `=` (empty file)
- `[auth]` (empty file)
- `[internal]` (empty file)
- `CACHED` (empty file)
- `resolve` (empty file)
- `transferring` (empty file)
- `backup_20251108.sql` (empty file)

### Old Log Files (Archived to /logs/archive/)
- `docker_log1102`
- `installation.log`
- `install.log`
- `install-root.log`

### Old Backup Files
- `requirements.txt.backup-20251107-210655`
- `.env.backup-token`
- `infrastructure/docker/compose/docker-compose.teamcity.yml.backup-20251108-125532`
- `infrastructure/docker/compose/docker-compose.teamcity.yml.backup-20251108-184634`
- `infrastructure/docker/compose/backup_20251108.sql`

### Obsolete Migration Scripts (19 total)
**MUI Cleanup Scripts:**
- `scripts/complete-mui-removal.py`
- `scripts/final-mui-cleanup.py`
- `scripts/final-mui-purge.py`
- `scripts/fix-all-mui.py`
- `scripts/fix-mui-imports.js`
- `scripts/fix-mui-imports.py`
- `scripts/fix-remaining-icons.py`

**TypeScript Fix Scripts:**
- `scripts/python/aggressive_ts_fix.py`
- `scripts/python/final_typescript_fix.py`

**Test Fix Scripts:**
- `scripts/testing/fix_all_tests_direct.py`
- `scripts/testing/fix_generated_test_patterns.py`
- `scripts/testing/fix_generated_tests.py`
- `scripts/testing/fix_remaining_tests_phase3.py`
- `scripts/testing/fix_test_conflicts.py`
- `scripts/testing/fix_test_failures_phase3.py`
- `scripts/testing/fix_test_failures.py`
- `scripts/testing/fix_test_imports_v2.py`
- `scripts/testing/fix_test_imports.py`
- `scripts/testing/fix_test_skips.py`

---

## Update Actions Required

### If you have hardcoded paths in:

1. **Shell Scripts** - Update import/source paths
2. **Python Imports** - Check test discovery paths
3. **Documentation Links** - Update cross-references
4. **CI/CD Configurations** - Update file paths in workflows
5. **IDE Configurations** - Update workspace settings

### Search Commands to Find References

```bash
# Find references to moved files
grep -r "CODERABBIT_SETUP" .
grep -r "apps/dashboard/SECURITY.md" .
grep -r "__tests__" .
grep -r "verify-system-health.sh" .
```

---

## Questions?

If you cannot find a file that was previously in the repository:
1. Check this relocation map
2. Check `/docs/11-reports/` for status reports
3. Check `/docs/06-features/dashboard/` for dashboard docs
4. Check `/docs/08-operations/docker/` for infrastructure docs
5. Check the "Files DELETED" section above

---

*Generated during project cleanup on November 9, 2025*
