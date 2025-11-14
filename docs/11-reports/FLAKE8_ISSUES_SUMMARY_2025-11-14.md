# Flake8 Linting Issues Summary

**Date:** November 14, 2025
**Status:** Documented - Awaiting Fixes
**CI/CD Impact:** GitHub Actions failing on Step 6 (Flake8)
**Total Violations:** ~450

## Summary

The GitHub Actions CI/CD pipeline is currently failing due to flake8 linting violations in the `apps/backend/` codebase. This document summarizes the issues and provides a roadmap for resolution.

## Issue Breakdown

| Category | Count | Severity |
|----------|-------|----------|
| Unused Imports (F401) | ~60 | Low |
| Undefined Names (F821) | ~35 | **Critical** |
| Unused Variables (F841) | ~60 | Medium |
| Line Too Long (E501) | ~80 | Low |
| Star Imports (F403/F405) | ~30 | Medium |
| Whitespace (W291/W293) | ~40 | Low |
| Bare Except (E722) | ~25 | Medium |
| Import Order (E402) | ~15 | Low |
| Other | ~105 | Low-Medium |

## Critical Issues (Blocking CI/CD)

### 1. Missing Imports (F821) - **High Priority**

**Files:**
- `apps/backend/api/v1/endpoints/mobile.py` - Missing `timezone` (6 occurrences)
- `apps/backend/api/v1/endpoints/storage_bulk.py` - Missing `timedelta` (2 occurrences)
- `apps/backend/api/v1/endpoints/storage_ws.py` - Missing `timedelta` (2 occurrences)
- `apps/backend/services/analytics_advanced.py` - Missing `timezone`, `distinct` (10+ occurrences)
- `apps/backend/api/v1/endpoints/ai_chat.py` - Missing LangChain imports

**Required Imports:**
```python
# DateTime imports
from datetime import timezone, timedelta

# SQLAlchemy imports
from sqlalchemy import distinct

# LangChain imports
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import END
from langgraph.checkpoint.sqlite import SqliteSaver
```

### 2. Star Imports (F403/F405) - **Medium Priority**

**File:** `apps/backend/agents/__init__.py`

Replace:
```python
from .agent import *
from .agent_classes import *
```

With explicit imports:
```python
from .agent import BaseAgent, AgentConfig, TaskResult
from .agent_classes import ContentAgent, QuizAgent, TerrainAgent
```

## Recommended Fixing Order

### Phase 1: Quick Wins (30 minutes)
1. ✅ Add missing datetime imports
2. ✅ Add missing SQLAlchemy imports
3. ✅ Add missing LangChain imports
4. Remove unused imports (automated)

### Phase 2: Code Quality (2 hours)
1. Fix bare except clauses
2. Remove/mark unused variables
3. Replace star imports
4. Fix import order

### Phase 3: Line Length (2 hours)
1. Break long lines
2. Refactor complex expressions

### Phase 4: Polish (1 hour)
1. Fix whitespace issues
2. Rename ambiguous variables
3. Optimize f-strings

## Manual Fix Required

Due to the complexity of some files and the risk of breaking existing functionality, **automated fixes are not recommended**. Each file should be reviewed and fixed manually to ensure:

1. Imports are added at the correct location
2. No functionality is broken
3. Type hints remain valid
4. Code formatting is preserved

## Validation

After fixing, run:
```bash
# Test specific file
flake8 apps/backend/path/to/file.py --max-line-length=120 --extend-ignore=E203,W503

# Test all backend
flake8 apps/backend/ --max-line-length=120 --extend-ignore=E203,W503
```

## Next Steps

1. **Immediate:** Manually add missing imports to critical files
2. **Short-term:** Clean up unused imports and variables
3. **Medium-term:** Refactor long lines and improve code quality

## Related Issues

- GitHub Actions failing: Step 6 (Run Flake8)
- CI/CD pipeline blocked
- Cannot deploy until linting passes

## Resources

- Flake8 Docs: https://flake8.pycqa.org/
- ToolBoxAI Standards: See `/CLAUDE.md`
- Error Codes: https://pycodestyle.pycqa.org/

---

**Next Review:** After Phase 1 completion
**Owner:** Development Team
**Priority:** High - Blocking deployments
