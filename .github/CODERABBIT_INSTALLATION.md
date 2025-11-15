# CodeRabbit GitHub App Installation Guide

**Status:** Installation Required
**Priority:** HIGH
**Estimated Time:** 5 minutes

---

## Installation Steps

### 1. Install CodeRabbit GitHub App

Visit: **https://github.com/apps/coderabbitai**

Click **"Install"** or **"Configure"**

### 2. Select Organization/Account

- Select: **GrayGhostDev**
- Or your personal account if it's a personal repository

### 3. Grant Repository Access

Choose one of:

**Option A: All Repositories** (Recommended)
- CodeRabbit will work on all current and future repos
- Easier management

**Option B: Select Repositories**
- Choose: **ToolboxAI-Solutions**
- Can add more repos later

### 4. Grant Permissions

CodeRabbit needs these permissions (all READ or READ/WRITE):

#### Required Permissions:
- ✅ **Pull requests** - Read & Write (to comment on PRs)
- ✅ **Contents** - Read (to read code)
- ✅ **Issues** - Read & Write (to create issues)
- ✅ **Metadata** - Read (repository metadata)
- ✅ **Workflows** - Read (to understand CI/CD)

#### Optional (Recommended):
- ✅ **Checks** - Read & Write (to create check runs)
- ✅ **Commit statuses** - Read & Write (to update PR status)

Click **"Install & Authorize"**

### 5. Verify Installation

After installation, verify:

1. Go to repository: https://github.com/GrayGhostDev/ToolboxAI-Solutions
2. Click **Settings** → **Integrations** → **GitHub Apps**
3. Verify **CodeRabbit** is listed and active

### 6. Test on a Pull Request

CodeRabbit will automatically review the next PR created.

**Quick Test:**
1. Create a small PR (can be a test branch)
2. Wait 1-2 minutes
3. Check for CodeRabbit comment with review

---

## Verification Checklist

After installation, verify:

- [ ] CodeRabbit app is visible in GitHub Apps settings
- [ ] Repository access includes ToolboxAI-Solutions
- [ ] Permissions are granted (pull requests, contents, issues)
- [ ] `.coderabbit.yaml` exists in repository root
- [ ] Test PR received CodeRabbit review comment

---

## Already Installed?

If CodeRabbit is already installed:

### Update Configuration
1. Go to: https://github.com/apps/coderabbitai
2. Click **"Configure"**
3. Verify ToolboxAI-Solutions is enabled
4. Check permissions are current

### Re-trigger Review
On an existing PR:
```
@coderabbit review
```

---

## Troubleshooting

### CodeRabbit Not Appearing

**Check:**
1. GitHub App installed? (Settings → Integrations)
2. Repository enabled? (CodeRabbit app settings)
3. Permissions granted? (Should have ✅ for all required)

**Fix:**
- Reinstall GitHub App
- Re-grant permissions
- Contact GitHub support if needed

### CodeRabbit Not Reviewing PRs

**Check:**
1. PR is not draft
2. PR title doesn't have "WIP" or "DO NOT REVIEW"
3. Configuration file exists: `.coderabbit.yaml`
4. Configuration is valid YAML

**Fix:**
```
# Manually trigger review
@coderabbit review

# Check config validity
cat .coderabbit.yaml | python -c "import yaml, sys; yaml.safe_load(sys.stdin)"
```

---

## Next Steps

After installation:

1. ✅ Read: `/docs/08-operations/ci-cd/coderabbit-setup-guide.md`
2. ✅ Print: `/docs/08-operations/ci-cd/coderabbit-quick-reference.md`
3. ✅ Create test PR to verify CodeRabbit works
4. ✅ Share with team in Slack

---

## Support

**Installation Issues:**
- CodeRabbit Support: support@coderabbit.ai
- Documentation: https://docs.coderabbit.ai

**Configuration Issues:**
- See: `/docs/08-operations/ci-cd/coderabbit-setup-guide.md`
- Team Slack: #coderabbit

---

**Ready to Install?**
👉 **https://github.com/apps/coderabbitai**

**ToolBoxAI Solutions Team**
