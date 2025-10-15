# Legacy Models Organization ID Addition Plan
## Phase 1, Task 1.3 - Final Step

**Date:** 2025-10-10
**File:** `database/models/models.py`
**Strategy:** Add explicit organization_id column (NOT TenantBaseModel conversion)

---

## Models Requiring organization_id (27 models)

### Educational Models (12 models)
1. ✅ **User** (line 103) - Migrate to user_modern.py (already has org_id)
2. ⏳ **Course** (line 165) - Add organization_id
3. ⏳ **Lesson** (line 202) - Add organization_id
4. ✅ **Content** (line 252) - Migrate to content_modern.py (already has org_id)
5. ⏳ **Quiz** (line 292) - Add organization_id
6. ⏳ **QuizQuestion** (line 333) - Add organization_id
7. ⏳ **QuizAttempt** (line 370) - Add organization_id
8. ⏳ **QuizResponse** (line 402) - Add organization_id
9. ⏳ **UserProgress** (line 429) - Add organization_id
10. ⏳ **Analytics** (line 462) - Add organization_id
11. ⏳ **Achievement** (line 496) - Add organization_id
12. ⏳ **UserAchievement** (line 528) - Add organization_id
13. ⏳ **Leaderboard** (line 555) - Add organization_id

### Platform Models (3 models)
14. ⏳ **Enrollment** (line 596) - Add organization_id
15. ⏳ **Session** (line 630) - Add organization_id
16. ⏳ **Class** (line 1231) - Add organization_id
17. ⏳ **ClassEnrollment** (line 1265) - Add organization_id

### Roblox Legacy Models (9 models)
18. ✅ **RobloxSession** (line 669) - Duplicate of roblox_models.py (skip)
19. ⏳ **RobloxContent** (line 734) - Add organization_id
20. ⏳ **RobloxPlayerProgress** (line 795) - Add organization_id
21. ⏳ **RobloxQuizResult** (line 868) - Add organization_id
22. ⏳ **RobloxAchievement** (line 945) - Add organization_id
23. ✅ **RobloxTemplate** (line 1005) - Duplicate of roblox_models.py (skip)
24. ⏳ **PluginRequest** (line 1301) - Add organization_id
25. ⏳ **RobloxDeployment** (line 1315) - Add organization_id
26. ⏳ **StudentProgress** (line 1096) - Add organization_id

### System Models (3 models - Global, no org_id)
27. ✅ **SchemaDefinition** (line 1128) - KEEP GLOBAL (no org_id)
28. ✅ **SchemaMapping** (line 1154) - KEEP GLOBAL (no org_id)
29. ✅ **AgentHealthStatus** (line 1177) - KEEP GLOBAL (migrate to agent_models.py)

### Integration Model (1 model)
30. ⏳ **IntegrationEvent** (line 1201) - Add organization_id

---

## Implementation Pattern

### Standard Addition (for all tenant-scoped models)

```python
from sqlalchemy.dialects.postgresql import UUID

class ModelName(Base):
    __tablename__ = "table_name"

    id = Column(Integer, primary_key=True, index=True)

    # ADD THIS BLOCK:
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ... existing fields
```

### Updated Indexes

Update `__table_args__` to include organization_id:

```python
# Before
__table_args__ = (
    Index("idx_model_field", "field"),
)

# After
__table_args__ = (
    Index("idx_model_org_field", "organization_id", "field"),
)
```

---

## Models Summary

**Total Legacy Models:** 30
**Need organization_id:** 22 models
**Already have org_id (modern):** 2 models (User, Content)
**Duplicates (skip):** 2 models (RobloxSession, RobloxTemplate)
**Global (no org_id):** 4 models (SchemaDefinition, SchemaMapping, AgentHealthStatus, TerrainTemplate, QuizTemplate)

**Action Required:** Add organization_id to 22 models

---

## Execution Plan

Due to the large file size (1400+ lines), we'll add organization_id in batches:

### Batch 1: Educational Core (5 models) - Priority HIGH
- Course, Lesson, Quiz, QuizQuestion, QuizAttempt

### Batch 2: Assessment & Progress (5 models) - Priority HIGH
- QuizResponse, UserProgress, Analytics, Achievement, UserAchievement

### Batch 3: Platform Features (4 models) - Priority MEDIUM
- Leaderboard, Enrollment, Session, Class, ClassEnrollment

### Batch 4: Roblox Legacy (6 models) - Priority MEDIUM
- RobloxContent, RobloxPlayerProgress, RobloxQuizResult, RobloxAchievement
- PluginRequest, RobloxDeployment, StudentProgress

### Batch 5: Integration (1 model) - Priority LOW
- IntegrationEvent

---

## Important Notes

1. **Don't convert to TenantBaseModel** - Would break too much legacy code
2. **Add explicit organization_id column** - Simpler, less risk
3. **Update indexes** - Include organization_id in composite indexes
4. **Preserve Integer IDs** - Don't change to UUID (backwards compatibility)
5. **Data migration required** - Populate organization_id for existing records

---

**Status:** Ready to implement
**Estimated Time:** 2-3 hours
**Next Action:** Begin Batch 1 - Educational Core models
