# ============================================================================
# GitHub Copilot Autofix - Quick Start Guide
# ============================================================================

## Enable Copilot Autofix

GitHub Copilot Autofix must be enabled through the GitHub UI as it requires
repository admin permissions and GitHub Advanced Security license.

### Steps to Enable:

1. **Visit Repository Settings**
   ```
   https://github.com/GrayGhostDev/ToolboxAI-Solutions/settings/security_analysis
   ```

2. **Locate Copilot Autofix Section**
   - Scroll to "Code security and analysis"
   - Find "GitHub Copilot Autofix" section

3. **Enable the Feature**
   - Click "Enable" button
   - Confirm any prompts

4. **Verify Configuration**
   - Configuration file: `.github/copilot-autofix.yml`
   - Workflow ready: `.github/workflows/security.yml`

---

## Using Autofix Suggestions

### In Code Scanning Alerts

1. Navigate to: `Security` → `Code scanning`
2. Click on any alert
3. Look for "Suggested fix" section
4. Review the AI-generated fix
5. Options:
   - **Accept:** Create PR with fix
   - **Modify:** Edit suggestion before applying
   - **Reject:** Dismiss if incorrect

### In Pull Requests

When CodeQL detects issues in PRs:
1. Autofix suggestions appear as review comments
2. Click "Commit suggestion" to apply
3. Or modify the suggestion first
4. Fixes are committed automatically

### Command Line

```bash
# List alerts with autofix available
gh api repos/GrayGhostDev/ToolboxAI-Solutions/code-scanning/alerts \
  --jq '.[] | select(.tool.name == "CodeQL") | 
        {number, rule: .rule.id, severity: .rule.severity}'

# View specific alert details
gh api repos/GrayGhostDev/ToolboxAI-Solutions/code-scanning/alerts/ALERT_NUMBER
```

---

## Review Checklist

Before accepting any autofix suggestion:

- [ ] Understand the vulnerability
- [ ] Review the suggested fix code
- [ ] Check for unintended side effects
- [ ] Verify tests will pass
- [ ] Ensure code style consistency
- [ ] Validate security improvement
- [ ] Test in development environment
- [ ] Get security team approval (for critical fixes)

---

## Example Workflow

### Scenario: SQL Injection Alert

1. **Alert Appears**
   ```
   Alert: Unsanitized user input in SQL query
   File: apps/backend/api/users.py
   Line: 42
   ```

2. **Autofix Suggestion**
   ```python
   # Before (vulnerable):
   query = f"SELECT * FROM users WHERE id = {user_id}"
   
   # After (fixed):
   query = "SELECT * FROM users WHERE id = ?"
   params = (user_id,)
   ```

3. **Review**
   - ✅ Uses parameterized query
   - ✅ Prevents SQL injection
   - ✅ Maintains functionality
   - ✅ Tests should pass

4. **Apply**
   - Click "Create pull request"
   - PR created: `autofix/alert-123-sql-injection`
   - Review, test, merge

---

## Configuration

### Current Settings

**File:** `.github/copilot-autofix.yml`

**Key Settings:**
- Languages: Python, JavaScript, TypeScript
- Severity: error, warning, note
- Require approval: Yes (always)
- Auto-create PR: No (manual review required)
- Min confidence: 70%

### Customization

Edit `.github/copilot-autofix.yml` to:
- Add/remove languages
- Exclude specific rules
- Adjust confidence threshold
- Change PR settings
- Modify quality controls

---

## Responsible Use

### Always:
✅ Review suggestions carefully  
✅ Test fixes before deploying  
✅ Validate security improvements  
✅ Follow code review process  
✅ Document security decisions  

### Never:
❌ Blindly accept all suggestions  
❌ Skip testing  
❌ Deploy without review  
❌ Ignore failing tests  
❌ Apply fixes you don't understand  

---

## Support

### Documentation
- Implementation Guide: `docs/10-security/COPILOT_AUTOFIX_IMPLEMENTATION.md`
- GitHub Docs: https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/responsible-use-autofix-code-scanning

### Scripts
- Enable autofix: `bash scripts/security/enable_copilot_autofix.sh`
- Check status: `bash scripts/security/check_security_status.sh`

### Contacts
- Security Team: security-team@company.com
- GitHub Support: https://support.github.com

---

## Quick Reference

| Action | Command/Link |
|--------|--------------|
| Enable Autofix | https://github.com/GrayGhostDev/ToolboxAI-Solutions/settings/security_analysis |
| View Alerts | https://github.com/GrayGhostDev/ToolboxAI-Solutions/security/code-scanning |
| Configuration | `.github/copilot-autofix.yml` |
| Documentation | `docs/10-security/COPILOT_AUTOFIX_IMPLEMENTATION.md` |
| Enable Script | `bash scripts/security/enable_copilot_autofix.sh` |

---

**Status:** Ready to enable  
**Last Updated:** 2025-11-10  
**Next Steps:** Enable in repository settings
