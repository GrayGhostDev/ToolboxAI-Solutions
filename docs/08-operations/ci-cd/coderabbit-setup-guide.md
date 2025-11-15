# CodeRabbit AI Setup Guide

**Last Updated:** November 1, 2025
**Status:** ✅ Configured and Ready
**Priority:** HIGH - Critical for Test Coverage Improvement (21% → 85%)

---

## 📋 Overview

CodeRabbit is an AI-powered code review assistant integrated with our GitHub repository to provide automated, intelligent code reviews on every pull request. It's specifically configured to help improve our test coverage from 21% to our 85% target.

### What CodeRabbit Does

- 🔍 **Automated Code Review** - Reviews every PR automatically
- 🧪 **Test Coverage Analysis** - Identifies untested code and suggests specific test cases
- 🔒 **Security Scanning** - Flags potential security vulnerabilities
- 📊 **Coverage Impact** - Estimates coverage improvement for each change
- ✅ **Best Practices** - Ensures code follows ToolBoxAI standards
- 🎯 **Priority Focus** - Emphasizes zero-coverage security files

---

## 🚀 Quick Start

### For Developers

When you create a pull request, CodeRabbit will:

1. **Automatically review your code** within 1-2 minutes
2. **Comment on specific lines** with suggestions
3. **Generate test cases** for uncovered code
4. **Provide coverage estimates** for your changes
5. **Request changes** if critical issues found

### How to Interact with CodeRabbit

**In PR comments:**
```
@coderabbit help
```
Shows all available commands

```
@coderabbit review
```
Manually trigger a review

```
@coderabbit explain <file>:<line>
```
Get detailed explanation of code at specific line

```
@coderabbit generate tests for <file>
```
Request test case generation for a specific file

---

## 🔧 Installation & Verification

**Installation Status:** ✅ Already installed

### Step 1: Verify GitHub App Installation

1. Go to: https://github.com/apps/coderabbitai
2. Click **"Configure"**
3. Select **GrayGhostDev** organization
4. Ensure **ToolboxAI-Solutions** repository is selected
5. Grant required permissions:
   - ✅ Pull requests (read & write)
   - ✅ Contents (read)
   - ✅ Issues (read & write)
   - ✅ Metadata (read)

### Step 2: Verify Configuration File

The configuration file `.coderabbit.yaml` is in the repository root:

```bash
# Verify file exists
ls -la .coderabbit.yaml

# View configuration
cat .coderabbit.yaml
```

**Configuration Status:** ✅ Configured (November 15, 2025)

### Step 3: Test on a Pull Request

Create a test PR to verify CodeRabbit is working:

```bash
# Create a test branch
git checkout -b test/coderabbit-verification

# Make a small change (e.g., add a comment)
echo "# Test comment for CodeRabbit" >> apps/backend/main.py

# Commit and push
git add apps/backend/main.py
git commit -m "test: verify CodeRabbit integration"
git push origin test/coderabbit-verification

# Create PR via GitHub CLI
gh pr create --title "test: CodeRabbit verification" \
  --body "Testing CodeRabbit AI integration" \
  --base main
```

**Expected Behavior:**
- CodeRabbit should comment within 1-2 minutes
- You'll see a bot comment with review walkthrough
- Any issues will be highlighted with suggestions

---

## 📊 Configuration Details

### Review Profile: Assertive

Our configuration uses the **"assertive"** profile for thorough analysis:

- More comprehensive reviews
- Higher sensitivity to potential issues
- Detailed explanations and examples
- Specific test case generation

### Priority Areas

CodeRabbit focuses on these critical areas (in order):

#### 🔴 CRITICAL Priority - Zero Coverage Files
- `apps/backend/api/auth/**` - Authentication (0% coverage)
- `apps/backend/core/security/**` - Security infrastructure (0% coverage)

**What CodeRabbit Does:**
- Flags every security vulnerability
- Generates specific pytest test cases
- Provides mocking strategies
- Estimates coverage impact

#### 🟡 HIGH Priority - Low Coverage Areas
- `core/agents/**` - Agent system (14-56% coverage)
- `apps/backend/core/**` - Core infrastructure

**What CodeRabbit Does:**
- Suggests integration test scenarios
- Provides LangChain/LangGraph test patterns
- Recommends async testing approaches

#### 🟢 MEDIUM Priority - Moderate Coverage
- `apps/backend/api/v1/endpoints/**` - API endpoints
- `apps/dashboard/src/components/**` - Frontend components

**What CodeRabbit Does:**
- Reviews input validation
- Checks error handling consistency
- Suggests edge case tests

### Excluded Files

CodeRabbit skips these files (no review needed):

```yaml
- node_modules/**
- dist/** and build/**
- __pycache__/** and *.pyc
- venv/** and .venv/**
- coverage/** and .coverage
- Archive/**
```

---

## 🎯 Using CodeRabbit for Test Coverage

### Example: Adding Tests for Zero-Coverage File

**Scenario:** You're working on `apps/backend/api/auth/auth_secure.py` (0% coverage)

1. **Create a PR** with your changes
2. **CodeRabbit will comment** with:
   ```
   🔴 CRITICAL PRIORITY - Zero Test Coverage on Authentication

   📊 Coverage Impact Analysis
   - Current coverage: 0%
   - Target coverage: 85%
   - This change impact: +8% (if tests added)

   ✅ Actionable Test Cases

   # Test successful authentication
   async def test_authenticate_user_success():
       # ... specific test code ...

   # Test invalid credentials
   async def test_authenticate_user_invalid_password():
       # ... specific test code ...

   🔧 Required Mocking
   - Mock Clerk client with pytest-mock
   - Fixture for test user credentials
   ```

3. **Implement suggested tests** in `tests/backend/api/auth/test_auth_secure.py`
4. **Push changes** - CodeRabbit will re-review and update coverage estimate

### Example Commands

**Request test generation:**
```
@coderabbit generate tests for apps/backend/api/auth/auth_secure.py
```

**Ask for coverage analysis:**
```
@coderabbit analyze coverage impact
```

**Request security review:**
```
@coderabbit review security for apps/backend/core/security/
```

---

## 📝 Best Practices

### Do's ✅

1. **Review CodeRabbit comments carefully** - They're specific to ToolBoxAI stack
2. **Implement suggested tests** - They target coverage gaps
3. **Ask for clarification** - Use `@coderabbit explain`
4. **Use coverage estimates** - Prioritize high-impact tests
5. **Address security findings** - Especially for auth/security code

### Don'ts ❌

1. **Don't ignore CRITICAL priority comments** - Security issues must be fixed
2. **Don't dismiss test suggestions** - They're targeted to coverage goals
3. **Don't skip mocking recommendations** - Required for proper test isolation
4. **Don't merge without addressing CodeRabbit** - Unless marked as false positive

### Working with CodeRabbit Reviews

**When CodeRabbit requests changes:**

```markdown
✅ Good Response:
"@coderabbit Thanks for the test suggestions. I've implemented all
three test cases and added the recommended mocking. Coverage for
this file is now 87%."

❌ Bad Response:
"Tests are not needed for this file."
(Without justification or discussion)
```

**When you disagree with CodeRabbit:**

```markdown
✅ Good Response:
"@coderabbit I understand the suggestion, but we intentionally skip
testing this function because [reason]. We've documented this in
the code comments. Can you confirm this approach is acceptable?"

❌ Bad Response:
"Ignored."
```

---

## 🔍 Troubleshooting

### CodeRabbit Not Commenting on PR

**Possible causes:**

1. **PR is marked as draft** - CodeRabbit skips drafts by default
   - Solution: Mark PR as "Ready for review"

2. **PR title contains ignore keywords** - "WIP", "DO NOT REVIEW", "DRAFT"
   - Solution: Update PR title

3. **No code changes** - Only documentation/config changes
   - Solution: This is expected behavior

4. **GitHub App not installed**
   - Solution: Follow "Installation & Verification" steps above

5. **Configuration file has errors**
   - Solution: Validate YAML at https://yaml-editor-ochre.vercel.app/embed

### CodeRabbit Comments Are Too Generic

**Possible causes:**

1. **File not in priority paths** - Review focus is on specific files
   - Solution: Check `.coderabbit.yaml` path_instructions

2. **Configuration out of date**
   - Solution: Pull latest main branch

### How to Manually Trigger Review

```bash
# In PR comments
@coderabbit review

# Or re-push to trigger
git commit --amend --no-edit
git push --force-with-lease
```

---

## 📚 Configuration Reference

### Key Configuration Sections

#### 1. Review Settings
```yaml
reviews:
  profile: "assertive"          # Thorough analysis
  auto_review:
    enabled: true               # Auto-review all PRs
    drafts: false               # Skip draft PRs
  request_changes_workflow: true # Auto request changes
```

#### 2. Path Instructions (Critical)
```yaml
path_instructions:
  - path: "apps/backend/api/auth/**"
    instructions: |
      🔴 CRITICAL PRIORITY - Zero Test Coverage
      [Specific instructions for auth files]
```

**Customize for new critical paths:**
1. Edit `.coderabbit.yaml`
2. Add path under `path_instructions`
3. Provide specific review focus
4. Commit and push

#### 3. Exclusions
```yaml
path_filters:
  - "!node_modules/**"          # Exclude dependencies
  - "**/*.py"                   # Include Python files
```

### Updating Configuration

```bash
# Edit configuration
nano .coderabbit.yaml

# Test YAML validity (copy content to):
# https://yaml-editor-ochre.vercel.app/embed

# Commit changes
git add .coderabbit.yaml
git commit -m "chore: update CodeRabbit configuration"
git push

# CodeRabbit will use new config on next PR
```

---

## 🎓 Advanced Features

### 1. Knowledge Base Learning

CodeRabbit learns from:
- Your repository patterns
- Past PR reviews
- Team preferences
- Code style

**Status:** ✅ Enabled (`knowledge_base.learnings: true`)

### 2. Chat Mode

Interactive conversation with CodeRabbit:

```
@coderabbit chat
```

Then ask questions:
```
What's the current coverage for the auth module?
Suggest a testing strategy for LangChain agents
Review security best practices for this endpoint
```

### 3. Early Access Features

**Status:** ✅ Enabled (`early_access: true`)

Benefits:
- Latest AI model updates
- New review capabilities
- Enhanced coverage analysis

---

## 📈 Measuring Success

### Coverage Improvement Metrics

Track these metrics to measure CodeRabbit's impact:

**Before CodeRabbit:**
- Overall coverage: 21%
- Zero-coverage files: 23 files
- Security coverage: 0%

**Target (with CodeRabbit):**
- Overall coverage: 85%
- Zero-coverage files: 0 files
- Security coverage: 95%+

### Weekly Check-ins

```bash
# Run coverage report
pytest --cov=apps/backend --cov-report=term-missing

# Compare to baseline
# Document improvement in weekly reports
```

**Report Template:**
```markdown
## CodeRabbit Impact - Week of [Date]

### Coverage Metrics
- Overall: X% (was Y%, +Z%)
- Auth module: X% (was 0%, +X%)
- Security module: X% (was 0%, +X%)

### PRs Reviewed
- Total PRs: X
- CodeRabbit comments: Y
- Tests added: Z

### Key Improvements
1. [File] - Added tests, coverage +X%
2. [File] - Fixed security issue, added tests
```

---

## 🔗 Resources

### CodeRabbit Documentation
- **Main Docs:** https://docs.coderabbit.ai
- **Configuration Reference:** https://docs.coderabbit.ai/reference/configuration
- **Commands Reference:** https://docs.coderabbit.ai/guides/review-instructions

### ToolBoxAI-Specific Resources
- **Test Coverage Report:** `/docs/11-reports/test-coverage-analysis.md`
- **Testing Strategy:** `/docs/08-operations/testing/testing-strategy.md`
- **CI/CD Pipeline:** `/docs/08-operations/ci-cd/main-pipeline.md`

### YAML Validation
- **Editor:** https://yaml-editor-ochre.vercel.app/embed
- **Validator:** https://www.yamllint.com/

---

## 👥 Team Responsibilities

### All Developers
- ✅ Review CodeRabbit comments on your PRs
- ✅ Implement suggested test cases
- ✅ Address CRITICAL security findings
- ✅ Ask questions if suggestions unclear

### Code Reviewers
- ✅ Review CodeRabbit analysis before human review
- ✅ Ensure suggested tests are implemented
- ✅ Verify coverage estimates are accurate
- ✅ Approve PRs only after CodeRabbit issues resolved

### Tech Lead / Maintainers
- ✅ Monitor CodeRabbit configuration effectiveness
- ✅ Update path_instructions for new critical files
- ✅ Track coverage improvement metrics
- ✅ Adjust configuration based on team feedback

---

## 📞 Support

### Issues with CodeRabbit

**For configuration issues:**
1. Check this guide first
2. Validate YAML syntax
3. Review GitHub App permissions
4. Contact: tech-lead@toolboxai.solutions

**For false positives:**
```
@coderabbit This is a false positive because [reason].
Please update your analysis.
```

**For missing features:**
- Suggest improvements in team Slack #coderabbit channel
- Update `.coderabbit.yaml` via PR
- Document in `/docs/08-operations/ci-cd/`

---

## ✅ Verification Checklist

After reading this guide, verify:

- [ ] CodeRabbit GitHub App is installed on repository
- [ ] `.coderabbit.yaml` exists in repository root
- [ ] Configuration file is valid YAML
- [ ] You understand how to interact with CodeRabbit in PRs
- [ ] You know how to request test generation
- [ ] You understand priority areas (auth, security, agents)
- [ ] You know where to find CodeRabbit documentation
- [ ] You understand team responsibilities

---

**ToolBoxAI Solutions Engineering Team**
*Building the future of education with AI-powered code quality*

**Next Update:** December 15, 2025
**Maintained By:** DevOps & QA Team
