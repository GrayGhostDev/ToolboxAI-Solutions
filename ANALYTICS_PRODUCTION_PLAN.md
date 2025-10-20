# Analytics Endpoints Production Implementation Plan

**Date:** October 11, 2025
**Status:** IN PROGRESS
**Priority:** HIGH - Production readiness

---

## Executive Summary

The analytics.py file (904 lines) contains **ALL HARDCODED SAMPLE DATA** and needs to be replaced with real database queries for production use.

**Current State:**
- 9 analytics endpoints with hardcoded data
- 4 additional routers (gamification, compliance, users, schools) with sample data
- No database integration - all returns static values
- **Cannot be used in production**

**Required Action:**
Replace all hardcoded data with real database queries using proper models and session management.

---

## Affected Files

### Main File
- `apps/backend/api/v1/endpoints/analytics.py` (904 lines)

### Database Models Available
- `User` - User data
- `Class`, `ClassEnrollment` - Class/enrollment data
- `UserProgress`, `StudentProgress` - Progress tracking
- `Analytics` - Dedicated analytics table
- `Leaderboard` - Leaderboard data
- `Quiz`, `QuizAttempt` - Quiz/assessment data
- `Enrollment` - Course enrollments
- `Course`, `Lesson`, `Content` - Educational content

---

## Endpoints Requiring Fixes

### Analytics Router (9 endpoints)

**1. GET `/overview`** (Lines 21-36)
- **Current:** Returns hardcoded numbers
- **Needed:** Query counts from User, Class, Quiz, UserProgress tables
- **Queries:**
  - Total/active students: `SELECT COUNT(*) FROM users WHERE role='student'`
  - Total classes: `SELECT COUNT(*) FROM classes WHERE is_active=true`
  - Average completion: `SELECT AVG(progress_percentage) FROM user_progress`
  - Average score: `SELECT AVG(score) FROM quiz_attempts`

**2. GET `/student-progress`** (Lines 39-75)
- **Current:** Returns hardcoded progress data
- **Needed:** Query UserProgress, Analytics, Leaderboard for specific student
- **Queries:**
  - Overall progress: `SELECT AVG(progress_percentage) FROM user_progress WHERE user_id=?`
  - Completed lessons: `SELECT COUNT(*) FROM user_progress WHERE progress_percentage >= 100`
  - XP earned: `SELECT SUM(xp_earned) FROM analytics WHERE user_id=?`
  - Rank: `SELECT rank FROM leaderboard WHERE user_id=? ORDER BY updated_at DESC LIMIT 1`

**3. GET `/weekly_xp`** (Lines 78-100)
- **Current:** Random XP generation
- **Needed:** Query Analytics table for last 7 days
- **Queries:**
  - Daily XP: `SELECT DATE(created_at), SUM(xp_earned) FROM analytics WHERE user_id=? AND created_at >= NOW() - INTERVAL '7 days' GROUP BY DATE(created_at)`

**4. GET `/subject_mastery`** (Lines 103-117)
- **Current:** Hardcoded subjects and mastery levels
- **Needed:** Query UserProgress grouped by subject
- **Queries:**
  - Subject mastery: `SELECT subject, AVG(progress_percentage) as mastery, COUNT(*) as topics_completed FROM user_progress WHERE user_id=? GROUP BY subject`

**5. GET `/trends/engagement`** (Lines 490-553)
- **Current:** Random trend data
- **Needed:** Query Analytics table for engagement metrics over time
- **Queries:**
  - Daily engagement: `SELECT DATE(created_at), COUNT(DISTINCT user_id) FROM analytics WHERE created_at BETWEEN ? AND ? GROUP BY DATE(created_at)`

**6. GET `/trends/content`** (Lines 556-629)
- **Current:** Random content trends
- **Needed:** Query Content, UserProgress for view/completion stats
- **Queries:**
  - Content views: `SELECT content_id, COUNT(*) as views FROM user_progress GROUP BY content_id ORDER BY views DESC`

**7. GET `/dashboard`** (Lines 632-739)
- **Current:** Aggregated hardcoded data
- **Needed:** Combine multiple queries from other endpoints
- **Dependencies:** Uses queries from `/overview`, `/trends/engagement`

**8. GET `/realtime`** (Lines 742-788)
- **Current:** Hardcoded metrics
- **Needed:** Query recent Analytics entries, system metrics
- **Queries:**
  - Active users: `SELECT COUNT(DISTINCT user_id) FROM analytics WHERE created_at >= NOW() - INTERVAL '5 minutes'`
  - Recent activities: `SELECT * FROM analytics ORDER BY created_at DESC LIMIT 10`

**9. GET `/summary`** (Lines 791-900)
- **Current:** Hardcoded summary stats
- **Needed:** Aggregate queries with optional filters
- **Queries:**
  - Total users: `SELECT COUNT(*) FROM users`
  - Completion rates: `SELECT AVG(progress_percentage) FROM user_progress GROUP BY subject`
  - Popular content: `SELECT content_id, COUNT(*) as views FROM user_progress GROUP BY content_id ORDER BY views DESC LIMIT 10`

### Gamification Router (1 endpoint)

**10. GET `/gamification/leaderboard`** (Lines 124-187)
- **Current:** Hardcoded leaderboard with fake names
- **Needed:** Query Leaderboard table with real user data
- **Queries:**
  - Leaderboard: `SELECT user_id, xp, level, rank FROM leaderboard ORDER BY xp DESC LIMIT ?`
  - User stats: `SELECT rank, previous_rank FROM leaderboard WHERE user_id=?`

### Compliance Router (1 endpoint)

**11. GET `/compliance/status`** (Lines 194-254)
- **Current:** Hardcoded compliance data
- **Needed:** Either remove (no compliance table) OR create compliance tracking system
- **Decision:** DEFER - requires compliance infrastructure first

### Users Router (2 endpoints)

**12. GET `/users/`** (Lines 261-325)
- **Current:** Hardcoded user list
- **Needed:** Query User table with filters
- **Queries:**
  - List users: `SELECT * FROM users WHERE role=? AND (username LIKE ? OR email LIKE ?) LIMIT ? OFFSET ?`

**13. GET `/users/{user_id}`** (Lines 328-353)
- **Current:** Hardcoded user profile
- **Needed:** Query User table for specific user
- **Queries:**
  - Get user: `SELECT * FROM users WHERE id=?`
  - User stats: `SELECT COUNT(*) FROM classes WHERE teacher_id=?` (for teachers)

### Schools Router (3 endpoints)

**14. GET `/schools/`** (Lines 360-416)
- **Current:** Hardcoded school list
- **Needed:** Either use Organization table OR defer
- **Decision:** DEFER - no School model exists, use Organization instead

**15. GET `/schools/{school_id}`** (Lines 419-450)
- **Decision:** DEFER - no School model

**16. POST `/schools/`** (Lines 453-486)
- **Decision:** DEFER - no School model

---

## Implementation Pattern

### Standard Pattern for Each Endpoint

```python
@analytics_router.get("/endpoint")
async def get_endpoint_data(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Endpoint description."""

    try:
        await database_service.initialize()

        # Authorization check
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Admin only")

        # Database queries
        query = select(Model).where(conditions)
        result = await session.execute(query)
        data = result.scalars().all()

        # Process and return
        return {
            "key": processed_data,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch data"
        )
```

---

## Implementation Steps

### Phase 1: Core Analytics (Priority 1)
**Estimated Time:** 4-6 hours

1. ✅ Create backup of original analytics.py
2. ⚠️ Add session dependency to all endpoints (IN PROGRESS)
3. ⚠️ Implement `/overview` with real queries (IN PROGRESS)
4. ⚠️ Implement `/student-progress` with real queries (PARTIAL)
5. Implement `/weekly_xp` with real queries
6. Implement `/subject_mastery` with real queries

### Phase 2: Trends & Dashboard (Priority 2)
**Estimated Time:** 3-4 hours

7. Implement `/trends/engagement` with real queries
8. Implement `/trends/content` with real queries
9. Implement `/dashboard` (combines other endpoints)
10. Implement `/realtime` with real queries
11. Implement `/summary` with filters

### Phase 3: Supporting Endpoints (Priority 3)
**Estimated Time:** 2-3 hours

12. Implement `/gamification/leaderboard` with real queries
13. Implement `/users/` list endpoint
14. Implement `/users/{user_id}` get endpoint

### Phase 4: Deferred Items (Priority 4)
**Estimated Time:** TBD

15. Decide on compliance tracking approach
16. Evaluate need for schools endpoints vs organizations
17. Create tests for all analytics endpoints

---

## Database Schema Requirements

### Existing Tables (Available)
- ✅ `users` - User data
- ✅ `classes` - Class data
- ✅ `class_enrollments` - Enrollment data
- ✅ `user_progress` - Progress tracking
- ✅ `analytics` - Analytics events
- ✅ `leaderboard` - Leaderboard rankings
- ✅ `quizzes` - Quiz definitions
- ✅ `quiz_attempts` - Quiz submissions

### Missing/Needed Tables
- ❌ `compliance_audits` - For compliance tracking
- ❌ `schools` OR use `organizations` - For school management
- ❌ `user_achievements` - For badge tracking
- ❌ `activity_logs` - For recent activity tracking
- ❌ `streak_tracking` - For daily streak data

---

## Testing Strategy

### Unit Tests Needed
- Test each endpoint with mocked database session
- Verify authorization checks work correctly
- Test query logic with sample data
- Verify error handling

### Integration Tests Needed
- Test with real database (test database)
- Verify data aggregation is correct
- Test performance with large datasets
- Verify caching if implemented

---

## Performance Considerations

### Optimization Needed
1. **Add database indexes:**
   - `user_progress (user_id, created_at)`
   - `analytics (user_id, created_at)`
   - `quiz_attempts (user_id, completed_at)`
   - `leaderboard (user_id, updated_at)`

2. **Implement caching:**
   - Cache `/overview` for 5 minutes
   - Cache `/leaderboard` for 1 minute
   - Cache `/trends/*` for 15 minutes

3. **Add pagination:**
   - All list endpoints need limit/offset
   - Prevent large data dumps

---

## Migration Strategy

### Option 1: In-Place Replacement (RISKY)
1. Backup analytics.py to analytics_backup.py
2. Replace all endpoints with production queries
3. Test thoroughly in development
4. Deploy with monitoring

### Option 2: Gradual Migration (SAFER)
1. Create analytics_v2.py with production queries
2. Route traffic to v2 endpoints gradually
3. Monitor for issues
4. Deprecate old endpoints after validation
5. Remove analytics.py (old) after 30 days

### Recommendation: **Option 2 (Gradual Migration)**

---

## Current Status

**Completed:**
- ✅ Analyzed analytics.py and identified all hardcoded data
- ✅ Created production plan document
- ✅ Started analytics_production.py with 2 endpoints (overview, student-progress)

**In Progress:**
- ⚠️ Implementing real database queries for core endpoints

**Blocked:**
- ❌ No compliance tracking system exists
- ❌ No schools table (use organizations instead?)
- ❌ Missing activity logs table for recent activity

**Next Steps:**
1. Complete Phase 1 core analytics endpoints (4 more endpoints)
2. Test endpoints with real database
3. Add proper error handling and logging
4. Create unit tests for each endpoint
5. Plan deployment strategy

---

## Estimated Completion

**Phase 1-3 (Core + Trends + Supporting):** 9-13 hours
**Testing & Documentation:** 3-4 hours
**Total Estimated Time:** 12-17 hours

**Recommended Approach:**
- Assign to dedicated developer
- Complete in 2-3 days
- Test thoroughly before production deployment
- Deploy using gradual migration strategy

---

*Created: October 11, 2025*
*Status: IN PROGRESS*
*Priority: HIGH - Production Blocker*
