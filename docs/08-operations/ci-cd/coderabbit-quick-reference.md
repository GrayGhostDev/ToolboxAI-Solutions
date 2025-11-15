# CodeRabbit Quick Reference Card

**For:** Developers creating PRs
**Last Updated:** November 15, 2025

---

## 🚀 Quick Commands

### In PR Comments

| Command | What It Does |
|---------|-------------|
| `@coderabbit help` | Show all available commands |
| `@coderabbit review` | Manually trigger code review |
| `@coderabbit explain <file>:<line>` | Explain code at specific line |
| `@coderabbit generate tests for <file>` | Request test case generation |
| `@coderabbit analyze coverage` | Get coverage impact analysis |
| `@coderabbit review security` | Focus on security issues |
| `@coderabbit chat` | Start interactive conversation |

---

## 🎯 Priority Levels

### 🔴 CRITICAL (Must Fix Before Merge)
- **Auth files** (`apps/backend/api/auth/**`) - 0% coverage
- **Security files** (`apps/backend/core/security/**`) - 0% coverage
- **Security vulnerabilities** - Any level

### 🟡 HIGH (Should Fix)
- **Agent system** (`core/agents/**`) - Low coverage (14-56%)
- **Core infrastructure** - Missing tests
- **Performance issues** - Significant impact

### 🟢 MEDIUM (Nice to Have)
- **API endpoints** - Input validation, error handling
- **Frontend components** - Accessibility, edge cases
- **Code quality** - Refactoring suggestions

---

## ✅ CodeRabbit Review Checklist

When you receive a CodeRabbit review:

### 1. Read the Coverage Impact
```
📊 Coverage Impact Analysis
- Current coverage: 21%
- This change: +8%
- Target: 85%
```

### 2. Check Priority Level
- 🔴 CRITICAL → **Must implement before merge**
- 🟡 HIGH → **Strongly recommended**
- 🟢 MEDIUM → **Consider for quality**

### 3. Review Test Suggestions
```python
✅ Actionable Test Cases

async def test_authenticate_user_success():
    # CodeRabbit provides specific test code
    pass
```

### 4. Implement or Respond
- ✅ **Implement**: Add tests, push changes
- 💬 **Discuss**: `@coderabbit <your question>`
- ❌ **Disagree**: Explain why with `@coderabbit`

---

## 📝 Good PR Practices

### Do This ✅

```markdown
## Changes
- Added user authentication endpoint
- Added 5 test cases (auth_secure.py coverage: 0% → 87%)
- Mocked Clerk client as suggested by CodeRabbit

## CodeRabbit Review
- Addressed all CRITICAL findings
- Implemented suggested security tests
- Coverage impact: +8%
```

### Don't Do This ❌

```markdown
## Changes
- Added auth endpoint

(No mention of tests or CodeRabbit feedback)
```

---

## 🔍 Common CodeRabbit Findings

### "Add tests for this function"
**What to do:**
1. Check suggested test cases in comments
2. Create test file in `tests/backend/` or `tests/`
3. Implement tests with suggested mocking
4. Run `pytest --cov` to verify coverage
5. Push changes

### "Security vulnerability detected"
**What to do:**
1. Read the security explanation
2. Implement suggested fix
3. Add security test case
4. Re-run security scan
5. Mark as resolved with comment

### "Consider refactoring for readability"
**What to do:**
1. Review suggestion
2. If agreed: Refactor code
3. If disagreed: Explain reasoning to `@coderabbit`
4. Document decision in code comments

---

## 📊 Test Coverage Targets

| Area | Current | Target | Priority |
|------|---------|--------|----------|
| **Auth** | 0% | 95%+ | 🔴 CRITICAL |
| **Security** | 0% | 95%+ | 🔴 CRITICAL |
| **Agents** | 14-56% | 85% | 🟡 HIGH |
| **API** | 45% | 85% | 🟡 HIGH |
| **Frontend** | 35% | 80% | 🟢 MEDIUM |
| **Overall** | 21% | 85% | 🎯 GOAL |

---

## 🛠️ Troubleshooting

### CodeRabbit didn't review my PR
**Reasons:**
- PR is marked as "Draft" → Mark as "Ready for review"
- PR title has "WIP" or "DO NOT REVIEW" → Update title
- Only docs/config changes → No code to review

**Fix:**
```
@coderabbit review
```

### CodeRabbit suggestions seem wrong
**Response:**
```
@coderabbit I think this suggestion may not apply because [reason].
Can you clarify?
```

### Need more specific help
**Ask:**
```
@coderabbit explain the testing strategy for async database operations
```

---

## 📚 Example Interactions

### Request Test Generation
```
@coderabbit generate tests for apps/backend/api/auth/auth_secure.py

Focus on:
- User authentication success/failure
- Token validation
- Rate limiting
- Error handling
```

**CodeRabbit will respond with:**
- Specific pytest test cases
- Required fixtures and mocks
- Coverage impact estimate
- Implementation guidance

### Ask for Coverage Analysis
```
@coderabbit analyze coverage impact for this PR
```

**CodeRabbit will respond with:**
- Current coverage stats
- Expected coverage after PR
- High-impact files to test
- Coverage improvement roadmap

### Security Review Request
```
@coderabbit review security for apps/backend/core/security/session_manager.py

Check for:
- Session fixation vulnerabilities
- Token expiration handling
- Race conditions
```

**CodeRabbit will respond with:**
- Security vulnerability assessment
- Recommended fixes
- Security test cases
- Compliance notes (COPPA, FERPA)

---

## ⚡ Pro Tips

### 1. Use CodeRabbit Early
- Request review on work-in-progress
- Get test suggestions before writing tests
- Catch security issues before review

### 2. Learn from Suggestions
- CodeRabbit knows ToolBoxAI stack
- Patterns apply to similar code
- Build a mental library of best practices

### 3. Combine with Human Review
- CodeRabbit finds patterns, humans find context
- CodeRabbit suggests tests, humans validate completeness
- CodeRabbit flags issues, humans make final decisions

### 4. Ask Questions
- CodeRabbit is interactive
- Request clarification
- Ask for alternatives
- Request more examples

---

## 🎯 Success Metrics

### Your PR is Ready When:
- ✅ CodeRabbit has reviewed (no pending comments)
- ✅ All 🔴 CRITICAL issues addressed
- ✅ Coverage impact is positive (+X%)
- ✅ Tests implemented for zero-coverage code
- ✅ Security findings resolved
- ✅ Human reviewer approved

---

## 📞 Need Help?

**Configuration issues:**
- See: `/docs/08-operations/ci-cd/coderabbit-setup-guide.md`

**Test writing help:**
- See: `/docs/08-operations/testing/testing-strategy.md`

**CodeRabbit not working:**
- Ask in: #coderabbit Slack channel
- Tag: @tech-lead

---

**Print this and keep it handy! 📌**

**ToolBoxAI Solutions Engineering Team**
