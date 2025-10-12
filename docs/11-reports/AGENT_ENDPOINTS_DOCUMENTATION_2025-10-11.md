# Agent Endpoints Documentation - Phase 2 Days 17-18

**Date:** 2025-10-11
**Purpose:** Document actual agent endpoint implementation before creating tests

---

## API Surface Analysis

### File: agent_instances.py

**Router Prefix:** `/instances`
**Tags:** `["agent-instances"]`
**Authentication:** All endpoints require authentication
**Multi-Tenant:** All endpoints automatically scoped to organization

---

## Endpoints Implemented

### 1. List Agent Instances
**Method:** `GET /instances`
**Function:** `list_agent_instances()`
**Auth:** Requires active user
**Returns:** `AgentInstanceListResponse`

**Query Parameters:**
- `status_filter`: Optional[str] - Filter by agent status
- `agent_type_filter`: Optional[str] - Filter by agent type
- `page`: int (default 1, min 1) - Page number
- `page_size`: int (default 50, min 1, max 100) - Items per page

**Response Schema:**
```python
{
    "items": List[AgentInstanceResponse],
    "total": int,
    "page": int,
    "page_size": int,
    "has_more": bool
}
```

**Multi-Tenant Security:**
- Automatically filtered by organization_id
- RLS policies enforce database-level isolation
- No cross-organization data leakage

**Test Scenarios:**
1. List all agents (no filters)
2. Filter by status
3. Filter by agent_type
4. Pagination (page 1, page 2)
5. Page size validation (min 1, max 100)
6. Empty result set
7. Organization isolation (cannot see other org's agents)

---

### 2. Create Agent Instance
**Method:** `POST /instances`
**Function:** `create_agent_instance()`
**Auth:** Requires active user
**Status:** 201 Created
**Returns:** `AgentInstanceResponse`

**Request Body:** `AgentInstanceCreate`
```python
{
    "agent_id": str,  # Unique identifier
    "agent_type": str,  # CONTENT_GENERATOR, etc.
    "configuration": Optional[dict]  # Agent config
}
```

**Response:** Full agent instance with:
- id (UUID)
- agent_id (str)
- agent_type (str)
- status (str) - Set to "INITIALIZING"
- organization_id (UUID) - Auto-set from user
- created_by_id (UUID) - Auto-set from user
- created_at, updated_at
- configuration (dict)

**Validation:**
- agent_id must be unique within organization
- Returns 400 if duplicate agent_id in organization

**Multi-Tenant Security:**
- organization_id automatically set from current user
- Cannot create agents for other organizations
- created_by_id tracks who created the agent

**Test Scenarios:**
1. Create agent successfully
2. Create with minimal data (no configuration)
3. Create with full configuration
4. Duplicate agent_id in same organization (400)
5. agent_id can duplicate in different organization (allowed)
6. organization_id auto-set correctly
7. created_by_id tracks user
8. Initial status is "INITIALIZING"

---

### 3. Get Agent Instance
**Method:** `GET /instances/{agent_id}`
**Function:** `get_agent_instance()`
**Auth:** Requires active user
**Returns:** `AgentInstanceResponse`

**Path Parameters:**
- `agent_id`: str - Unique identifier of the agent

**Response:** Full agent instance details

**Error Cases:**
- 404 if agent not found
- 404 if agent belongs to different organization (no information leakage)

**Multi-Tenant Security:**
- Query includes organization_id filter
- Returns 404 for cross-organization access attempts
- No information about existence in other organizations

**Test Scenarios:**
1. Get existing agent successfully
2. Get non-existent agent (404)
3. Get agent from different organization (404)
4. Verify all fields returned correctly

---

### 4. Update Agent Instance
**Method:** `PUT /instances/{agent_id}`
**Function:** `update_agent_instance()`
**Auth:** Requires active user
**Returns:** `AgentInstanceResponse`

**Path Parameters:**
- `agent_id`: str - Unique identifier of the agent

**Request Body:** `AgentInstanceUpdate`
```python
{
    "status": Optional[str],  # New status
    "configuration": Optional[dict]  # Updated config
}
```

**Response:** Updated agent instance

**Behavior:**
- Only updates provided fields (partial update)
- updated_by_id set to current user
- updated_at automatically updated

**Error Cases:**
- 404 if agent not found
- 404 if agent belongs to different organization

**Multi-Tenant Security:**
- Query includes organization_id filter
- Cannot update agents from other organizations
- updated_by_id tracks who made changes

**Test Scenarios:**
1. Update status only
2. Update configuration only
3. Update both fields
4. Partial update (only one field)
5. Update non-existent agent (404)
6. Update agent from different organization (404)
7. updated_by_id tracks user
8. Verify updated_at changes

---

### 5. Delete Agent Instance
**Method:** `DELETE /instances/{agent_id}`
**Function:** `delete_agent_instance()`
**Auth:** Requires active user
**Status:** 204 No Content

**Path Parameters:**
- `agent_id`: str - Unique identifier of the agent

**Response:** Empty (204 No Content on success)

**Error Cases:**
- 404 if agent not found
- 404 if agent belongs to different organization

**Multi-Tenant Security:**
- Query includes organization_id filter
- Cannot delete agents from other organizations
- Deletion logged for audit trail

**Test Scenarios:**
1. Delete existing agent successfully (204)
2. Delete non-existent agent (404)
3. Delete agent from different organization (404)
4. Verify agent actually deleted (GET returns 404)
5. Deletion logged correctly

---

### 6. Get Agent Executions
**Method:** `GET /instances/{agent_id}/executions`
**Function:** `get_agent_executions()`
**Auth:** Requires active user
**Returns:** `List[dict]`

**Path Parameters:**
- `agent_id`: str - Unique identifier of the agent

**Query Parameters:**
- `limit`: int (default 50, min 1, max 100) - Maximum executions to return

**Response:** List of execution records
```python
[
    {
        "id": str (UUID),
        "execution_id": str,
        "status": str,
        "created_at": str (ISO format),
        "completed_at": Optional[str] (ISO format)
    }
]
```

**Behavior:**
- Returns most recent executions first (DESC order)
- Verifies agent belongs to organization first
- Returns empty list if no executions

**Error Cases:**
- 404 if agent not found or no access

**Multi-Tenant Security:**
- Verifies agent belongs to current organization first
- Execution query also filtered by organization_id (defense in depth)
- Returns 404 for cross-organization access

**Test Scenarios:**
1. Get executions for agent with history
2. Get executions for agent with no history (empty list)
3. Limit parameter validation (default 50)
4. Limit parameter (custom value)
5. Limit max validation (max 100)
6. Agent not found (404)
7. Agent from different organization (404)
8. Executions ordered by created_at DESC

---

### 7. Get Agent Metrics
**Method:** `GET /instances/{agent_id}/metrics`
**Function:** `get_agent_metrics()`
**Auth:** Requires active user
**Returns:** `dict`

**Path Parameters:**
- `agent_id`: str - Unique identifier of the agent

**Response:** Agent metrics
```python
{
    "agent_id": str,
    "total_executions": int,
    "successful_executions": int,
    "failed_executions": int,
    "average_execution_time": float,
    "last_execution_time": Optional[str] (ISO format)
}
```

**Or if no metrics:**
```python
{
    "agent_id": str,
    "message": "No metrics available yet"
}
```

**Behavior:**
- Returns latest metrics for agent
- Returns friendly message if no metrics available

**Error Cases:**
- 404 if agent not found or no access

**Multi-Tenant Security:**
- Verifies agent belongs to current organization first
- Metrics query also filtered by organization_id
- Returns 404 for cross-organization access

**Test Scenarios:**
1. Get metrics for agent with metrics
2. Get metrics for agent with no metrics (friendly message)
3. Agent not found (404)
4. Agent from different organization (404)
5. Verify all metric fields returned

---

## Pydantic Schemas

### AgentInstanceCreate
```python
{
    "agent_id": str (required),
    "agent_type": str (required),
    "configuration": Optional[dict] (default {})
}
```

### AgentInstanceUpdate
```python
{
    "status": Optional[str],
    "configuration": Optional[dict]
}
```

### AgentInstanceResponse
```python
{
    "id": UUID,
    "agent_id": str,
    "agent_type": str,
    "status": str,
    "organization_id": UUID,
    "created_by_id": Optional[UUID],
    "created_at": str,
    "updated_at": Optional[str],
    "configuration": Optional[dict]
}
```

### AgentInstanceListResponse
```python
{
    "items": List[AgentInstanceResponse],
    "total": int,
    "page": int,
    "page_size": int,
    "has_more": bool
}
```

---

## Database Models Used

### AgentInstance
- From: `database.models.agent_models`
- Fields: id, agent_id, agent_type, status, organization_id, created_by_id, created_at, updated_at, configuration

### AgentExecution
- From: `database.models.agent_models`
- Fields: id, execution_id, agent_instance_id, status, organization_id, created_at, completed_at

### AgentMetrics
- From: `database.models.agent_models`
- Fields: id, agent_instance_id, organization_id, total_executions, successful_executions, failed_executions, average_execution_time, last_execution_time, created_at

---

## Dependencies Used

### Authentication
- `get_current_user` - Get current authenticated user
- `get_current_active_user` - Get current active user (not inactive)
- `get_current_organization_id` - Get user's organization ID

### Database
- `get_async_db` - Get async database session

---

## Test Plan Summary

**Total Test Scenarios Identified:** 48

**Breakdown by Endpoint:**
1. List Instances: 7 tests
2. Create Instance: 8 tests
3. Get Instance: 4 tests
4. Update Instance: 8 tests
5. Delete Instance: 5 tests
6. Get Executions: 8 tests
7. Get Metrics: 5 tests

**Additional Tests:**
- Pydantic schema validation: 3 tests

**Total Target:** 51 tests (exceeds 30 test requirement)

---

## Implementation Notes

### Multi-Tenant Pattern (Consistent Across All Endpoints)
1. organization_id injected via `Depends(get_current_organization_id)`
2. All queries filter by organization_id
3. 404 returned for cross-organization access (no information leakage)
4. Audit trail via created_by_id / updated_by_id

### Error Handling Pattern
```python
try:
    # Endpoint logic
except HTTPException:
    raise  # Re-raise HTTP exceptions
except Exception as e:
    logger.error(f"Failed to ...: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="...")
```

### Logging Pattern
```python
logger.info(
    f"Action performed: {details}",
    extra={
        "agent_id": agent_id,
        "organization_id": str(org_id),
        "user_id": str(current_user.id),
        # Additional context
    },
)
```

---

## Ready to Create Tests

All endpoints documented with:
- ✅ Actual function signatures verified
- ✅ Request/response schemas documented
- ✅ Multi-tenant security patterns identified
- ✅ Test scenarios defined
- ✅ Error cases cataloged

**Next Step:** Create test file with first 5 tests, verify they work, then scale to full suite.

---

**Documentation Complete:** 2025-10-11 21:50 PST
**Endpoints Analyzed:** 7
**Test Scenarios:** 51 identified
**Ready For:** Test implementation
