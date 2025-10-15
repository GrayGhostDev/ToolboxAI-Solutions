# RBAC Implementation Guide

**Role-Based Access Control (RBAC) System for ToolboxAI-Solutions**

Version: 1.0
Date: 2025-10-11
Author: System Architecture Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Role Definitions](#role-definitions)
4. [Permission System](#permission-system)
5. [Using RBAC Decorators](#using-rbac-decorators)
6. [Middleware Configuration](#middleware-configuration)
7. [Testing RBAC](#testing-rbac)
8. [Best Practices](#best-practices)
9. [Migration Guide](#migration-guide)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The RBAC system provides comprehensive role-based access control for the ToolboxAI platform. It supports:

- **Role Hierarchy**: Admin > Teacher > Student > Guest
- **Fine-grained Permissions**: Resource-level access control with scopes
- **Automatic Enforcement**: Middleware-level permission checking
- **Organization Isolation**: Multi-tenant support with organization-scoped permissions
- **Decorator-based Protection**: Simple API endpoint protection
- **Audit Logging**: Complete access attempt tracking

### Key Benefits

- **Security First**: Default-deny approach with explicit permission grants
- **Easy to Use**: Decorator-based API with minimal boilerplate
- **Scalable**: Supports complex permission requirements
- **Testable**: Comprehensive test coverage with mock-friendly design
- **Production Ready**: Performance optimized with permission caching

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Application                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              RBACMiddleware (Optional)                   │
│  • Automatic path-based permission checking             │
│  • Audit logging                                         │
│  • Organization context setting                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            Endpoint Decorators (Required)                │
│  • @require_role()                                       │
│  • @require_permission()                                 │
│  • @require_resource_access()                            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  RBACManager (Core)                      │
│  • Role definitions                                      │
│  • Permission checking logic                             │
│  • Resource access validation                            │
│  • Permission caching                                    │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
apps/backend/core/security/
├── rbac_manager.py          # Core RBAC logic (~400 lines)
├── rbac_decorators.py       # FastAPI decorators (~350 lines)
└── rbac_middleware.py       # Middleware layer (~280 lines)

apps/backend/api/v1/endpoints/
└── content_rbac_example.py  # Example implementation

tests/unit/core/security/
├── test_rbac_manager.py     # Manager tests (~280 lines)
├── test_rbac_decorators.py  # Decorator tests (~490 lines)
└── test_rbac_middleware.py  # Middleware tests (~580 lines)
```

---

## Role Definitions

### Role Hierarchy

```
┌──────────────────────────────────────────┐
│  ADMIN (Level 100)                       │
│  • Full system access                    │
│  • All permissions with :all scope       │
└──────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│  TEACHER (Level 50)                      │
│  • Organization-scoped access            │
│  • Manage classes and content            │
│  • Student supervision                   │
└──────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│  STUDENT (Level 10)                      │
│  • Limited read access                   │
│  • Own resource management               │
│  • Participate in classes                │
└──────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│  GUEST (Level 0)                         │
│  • Public content only                   │
│  • Minimal permissions                   │
└──────────────────────────────────────────┘
```

### Role Permissions Matrix

| Resource     | Admin | Teacher | Student | Guest |
|--------------|-------|---------|---------|-------|
| **Content**  |       |         |         |       |
| Create       | ✅ All | ✅ Org   | ❌      | ❌    |
| Read         | ✅ All | ✅ Org   | ✅ Org   | ✅ Public |
| Update       | ✅ All | ✅ Own   | ❌      | ❌    |
| Delete       | ✅ All | ✅ Own   | ❌      | ❌    |
| Publish      | ✅ All | ✅ Org   | ❌      | ❌    |
| **Users**    |       |         |         |       |
| Create       | ✅ All | ❌      | ❌      | ❌    |
| Read         | ✅ All | ✅ Org   | ✅ Own   | ❌    |
| Update       | ✅ All | ✅ Org   | ✅ Own   | ❌    |
| Delete       | ✅ All | ❌      | ❌      | ❌    |
| **Classes**  |       |         |         |       |
| Create       | ✅ All | ✅ Org   | ❌      | ❌    |
| Read         | ✅ All | ✅ Org   | ✅ Own   | ❌    |
| Update       | ✅ All | ✅ Own   | ❌      | ❌    |
| Delete       | ✅ All | ✅ Own   | ❌      | ❌    |
| **Agents**   |       |         |         |       |
| Execute      | ✅ All | ✅ Org   | ✅ Own   | ❌    |
| **Analytics**|       |         |         |       |
| Read         | ✅ All | ✅ Org   | ✅ Own   | ❌    |
| Export       | ✅ All | ✅ Org   | ❌      | ❌    |
| **System**   |       |         |         |       |
| Manage       | ✅     | ❌      | ❌      | ❌    |
| Configure    | ✅     | ❌      | ❌      | ❌    |
| Monitor      | ✅     | ❌      | ❌      | ❌    |

**Legend:**
- ✅ All = Access to all resources across all organizations
- ✅ Org = Access to resources within user's organization
- ✅ Own = Access only to user's own resources
- ✅ Public = Access to public resources only
- ❌ = No access

---

## Permission System

### Permission Format

Permissions follow the format: **`resource:action:scope`**

```
content:create:organization
│       │      │
│       │      └─ Scope (own, organization, all)
│       └──────── Action (create, read, update, delete, execute, manage)
└──────────────── Resource (content, agent, user, class, etc.)
```

### Permission Scopes

1. **`own`** - User can only access their own resources
   - Example: `content:update:own` (user can update their own content)
   - Scope check: `resource.created_by == user.id`

2. **`organization`** - User can access resources within their organization
   - Example: `content:read:organization` (user can read all content in their org)
   - Scope check: `resource.organization_id == user.organization_id`

3. **`all`** - User can access all resources (admin only)
   - Example: `user:delete:all` (admin can delete any user)
   - No scope restrictions

### Scope Inheritance

Higher scopes automatically grant lower scope permissions:

```
:all scope
  ├─ Includes :organization scope
  └─ Includes :own scope

:organization scope
  └─ Includes :own scope (within organization)
```

**Example:**
- If user has `content:create:all`, they also have:
  - `content:create:organization`
  - `content:create:own` (implied)

### Resource Types

```python
class ResourceType(str, Enum):
    CONTENT = "content"           # Educational content
    AGENT = "agent"              # AI agents
    ORGANIZATION = "organization"  # Organizations/tenants
    USER = "user"                # User accounts
    CLASS = "class"              # Classes/courses
    ANALYTICS = "analytics"       # Analytics and reports
    SYSTEM = "system"            # System administration
```

### Actions

```python
class Action(str, Enum):
    CREATE = "create"   # Create new resources
    READ = "read"       # View/list resources
    UPDATE = "update"   # Modify existing resources
    DELETE = "delete"   # Remove resources
    EXECUTE = "execute" # Execute/run operations
    MANAGE = "manage"   # Full management access
```

---

## Using RBAC Decorators

### Quick Start

```python
from fastapi import APIRouter, Depends
from database.models import User
from apps.backend.core.deps import get_current_user
from apps.backend.core.security.rbac_decorators import (
    require_role,
    require_permission,
    require_resource_access
)

router = APIRouter()

# Simple role check
@router.get("/admin/dashboard")
@require_role(["admin"])
async def admin_dashboard(user: User = Depends(get_current_user)):
    return {"message": "Welcome, admin!"}

# Permission check
@router.post("/content")
@require_permission("content:create:organization")
async def create_content(user: User = Depends(get_current_user)):
    # Only users with content:create:organization permission
    return {"message": "Content created"}

# Resource-level access with automatic ownership checking
@router.delete("/content/{content_id}")
@require_resource_access("content", "delete")
async def delete_content(
    content_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    # Decorator automatically checks:
    # 1. User has delete permission
    # 2. User owns resource OR has organization/all scope
    # 3. Returns 403 if denied, 404 if not found
    pass
```

### Available Decorators

#### 1. `@require_role(allowed_roles: List[str])`

Checks if user has one of the specified roles (uses hierarchy).

```python
@router.get("/teacher/dashboard")
@require_role(["admin", "teacher"])
async def teacher_dashboard(user: User = Depends(get_current_user)):
    # Both admins and teachers can access
    # Admin passes due to role hierarchy
    pass
```

**Parameters:**
- `allowed_roles`: List of role names that can access the endpoint

**Raises:**
- `401 Unauthorized`: If user is not authenticated
- `403 Forbidden`: If user doesn't have required role

#### 2. `@require_permission(permission: str)`

Checks if user has a specific permission.

```python
@router.post("/content/publish")
@require_permission("content:publish:organization")
async def publish_content(user: User = Depends(get_current_user)):
    # Only users with publish permission can access
    pass
```

**Parameters:**
- `permission`: Permission string in format "resource:action:scope"

**Raises:**
- `401 Unauthorized`: If user is not authenticated
- `403 Forbidden`: If user doesn't have permission

#### 3. `@require_permissions(permissions: List[str], require_all: bool = True)`

Checks multiple permissions with AND/OR logic.

```python
# Require ALL permissions (AND logic)
@router.post("/content/clone")
@require_permissions([
    "content:read:organization",
    "content:create:organization"
], require_all=True)
async def clone_content(user: User = Depends(get_current_user)):
    # User must have BOTH read AND create permissions
    pass

# Require ANY permission (OR logic)
@router.put("/content/{id}")
@require_permissions([
    "content:update:own",
    "content:update:organization"
], require_all=False)
async def update_content(user: User = Depends(get_current_user)):
    # User needs EITHER own OR organization scope
    pass
```

**Parameters:**
- `permissions`: List of permission strings
- `require_all`: If `True`, user needs ALL permissions. If `False`, user needs ANY one.

**Raises:**
- `401 Unauthorized`: If user is not authenticated
- `403 Forbidden`: If permission requirements not met

#### 4. `@require_resource_access(resource_type: str, action: str)`

Checks resource-level access with automatic ownership and organization validation.

```python
@router.delete("/content/{content_id}")
@require_resource_access("content", "delete")
async def delete_content(
    content_id: int,  # Must be named {resource_type}_id
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)  # Required for resource lookup
):
    # Decorator automatically:
    # 1. Looks up resource in database
    # 2. Checks user permission scope
    # 3. Validates ownership (for :own scope)
    # 4. Validates organization (for :organization scope)
    # 5. Returns appropriate error if access denied
    pass
```

**Parameters:**
- `resource_type`: Type of resource (content, agent, user, class, etc.)
- `action`: Action to perform (create, read, update, delete)

**Automatic Checks:**
1. **Scope resolution**: Determines user's permission scope (own/organization/all)
2. **Admin bypass**: Admins with `:all` scope skip all checks
3. **Resource lookup**: Queries database for resource
4. **Ownership validation**: For `:own` scope, checks `resource.created_by == user.id`
5. **Organization validation**: For `:organization` scope, checks `resource.organization_id == user.organization_id`

**Raises:**
- `401 Unauthorized`: If user is not authenticated
- `403 Forbidden`: If user doesn't have access to resource
- `404 Not Found`: If resource doesn't exist

**Requirements:**
- Path parameter must be named `{resource_type}_id` (e.g., `content_id`, `agent_id`)
- Database session must be provided via `db` parameter
- Resource model must have `created_by` and/or `organization_id` attributes

#### 5. `@require_organization_access()`

Ensures user belongs to an organization (for multi-tenant endpoints).

```python
@router.get("/organization/settings")
@require_organization_access()
async def get_org_settings(user: User = Depends(get_current_user)):
    # User guaranteed to have user.organization_id set
    return {"org_id": user.organization_id}
```

**Parameters:** None

**Raises:**
- `401 Unauthorized`: If user is not authenticated
- `403 Forbidden`: If user doesn't belong to an organization

#### 6. Convenience Decorators

Pre-configured role decorators for common use cases:

```python
from apps.backend.core.security.rbac_decorators import (
    require_admin,
    require_teacher,
    require_teacher_or_student
)

# Admin only
@router.get("/admin/users")
@require_admin
async def list_all_users(user: User = Depends(get_current_user)):
    pass

# Admin or Teacher
@router.post("/classes")
@require_teacher
async def create_class(user: User = Depends(get_current_user)):
    pass

# Admin, Teacher, or Student
@router.get("/dashboard")
@require_teacher_or_student
async def dashboard(user: User = Depends(get_current_user)):
    pass
```

### Decorator Composition

Decorators can be combined for layered security:

```python
@router.post("/organization/content")
@require_teacher
@require_organization_access()
@require_permission("content:create:organization")
async def create_org_content(user: User = Depends(get_current_user)):
    # User must:
    # 1. Have teacher role (or higher)
    # 2. Belong to an organization
    # 3. Have content creation permission
    pass
```

**Execution Order:** Decorators execute from bottom to top.

### Error Handling

All decorators raise FastAPI `HTTPException`:

```python
from fastapi import HTTPException, status

# 401 Unauthorized - Not authenticated
{
    "detail": "Authentication required"
}

# 403 Forbidden - Insufficient permissions
{
    "detail": "Insufficient permissions. Required: content:create:organization",
    "required_permission": "content:create:organization",
    "user_role": "student"
}

# 404 Not Found - Resource doesn't exist
{
    "detail": "Content not found"
}
```

---

## Middleware Configuration

### Enabling RBAC Middleware

Add middleware to your FastAPI application:

```python
from fastapi import FastAPI
from apps.backend.core.security.rbac_middleware import RBACMiddleware

app = FastAPI()

# Add RBAC middleware
app.add_middleware(RBACMiddleware)

# Middleware runs BEFORE endpoint handlers
# Provides automatic path-based permission checking
```

### Middleware Features

1. **Automatic Permission Checking**: Maps HTTP methods and paths to required permissions
2. **Public Path Bypass**: Skips RBAC for authentication, docs, health checks
3. **Audit Logging**: Logs all access attempts with user, permission, and outcome
4. **Organization Context**: Automatically sets organization context for queries

### Path Permission Mapping

Middleware automatically maps paths to permissions:

```python
# Example mappings in RBACMiddleware
path_permissions = {
    r"/api/v1/content/?.*": {
        "GET": "content:read:organization",
        "POST": "content:create:organization",
        "PUT": "content:update:own",
        "DELETE": "content:delete:own",
    },
    r"/api/v1/users/?.*": {
        "GET": "user:read:organization",
        "POST": "user:create:all",  # Admin only
        "DELETE": "user:delete:all",  # Admin only
    },
    r"/api/v1/system/?.*": {
        "GET": "system:monitor",
        "POST": "system:configure",
    },
}
```

### Public Paths

The following paths bypass RBAC checks:

```python
public_paths = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
}

bypass_patterns = [
    r"^/static/.*",
    r"^/api/health/.*",
    r"^/_internal/.*",
]
```

### Audit Logging

Middleware logs all access attempts:

```python
# Successful access (INFO level)
RBAC GRANTED: user=2 method=GET path=/api/v1/content permission=content:read:organization duration=5.23ms

# Denied access (WARNING level)
RBAC DENIED: user=3 method=POST path=/api/v1/content permission=content:create:organization duration=3.12ms
```

**Log Fields:**
- User ID (or "anonymous")
- HTTP method
- Request path
- Required permission
- Access decision (GRANTED/DENIED)
- Processing duration

### Disabling Audit Logging

```python
middleware = RBACMiddleware(app)
middleware.audit_enabled = False
```

### Organization Scoping Middleware

Automatically sets organization context for database queries:

```python
from apps.backend.core.security.rbac_middleware import OrganizationScopingMiddleware

app.add_middleware(OrganizationScopingMiddleware)

# Sets request.state.organization_id from user
# Can be used for automatic query scoping
```

---

## Testing RBAC

### Running Tests

```bash
# Run all RBAC tests
pytest tests/unit/core/security/ -v

# Run specific test file
pytest tests/unit/core/security/test_rbac_manager.py -v

# Run with coverage
pytest tests/unit/core/security/ --cov=apps.backend.core.security --cov-report=html
```

### Test Structure

```
tests/unit/core/security/
├── test_rbac_manager.py      # Core RBAC logic tests
├── test_rbac_decorators.py   # Decorator functionality tests
└── test_rbac_middleware.py   # Middleware integration tests
```

### Writing RBAC Tests

#### Testing with Mock Users

```python
import pytest
from unittest.mock import Mock
from apps.backend.core.security.rbac_manager import Role

@pytest.fixture
def mock_teacher_user():
    user = Mock()
    user.id = 2
    user.role = Role.TEACHER
    user.organization_id = uuid4()
    return user

def test_teacher_permissions(mock_teacher_user):
    from apps.backend.core.security.rbac_manager import rbac_manager

    # Teacher should have organization-scoped permissions
    assert rbac_manager.has_permission(
        mock_teacher_user,
        "content:create:organization"
    )

    # Teacher should NOT have all-scoped permissions
    assert not rbac_manager.has_permission(
        mock_teacher_user,
        "content:delete:all"
    )
```

#### Testing Decorators

```python
import pytest
from fastapi import HTTPException
from apps.backend.core.security.rbac_decorators import require_permission

@pytest.mark.asyncio
async def test_decorator_denies_insufficient_permissions(mock_student_user):
    @require_permission("content:create:organization")
    async def protected_endpoint(user: Mock):
        return {"message": "success"}

    # Student doesn't have create permission
    with pytest.raises(HTTPException) as exc_info:
        await protected_endpoint(user=mock_student_user)

    assert exc_info.value.status_code == 403
```

#### Testing Middleware

```python
import pytest
from starlette.requests import Request
from apps.backend.core.security.rbac_middleware import RBACMiddleware

@pytest.mark.asyncio
async def test_middleware_allows_public_paths(mock_app, mock_request):
    middleware = RBACMiddleware(mock_app)
    mock_request.url.path = "/api/health"
    mock_request.state.user = None  # No authentication

    async def call_next(request):
        return JSONResponse({"status": "ok"})

    response = await middleware.dispatch(mock_request, call_next)
    assert response.status_code == 200
```

### Test Coverage

Current test coverage:
- **RBACManager**: 89 tests covering role definitions, permissions, hierarchy
- **Decorators**: 36 tests covering all decorator types and combinations
- **Middleware**: 33 tests covering path mapping, audit logging, performance

**Total**: 158 comprehensive RBAC tests

---

## Best Practices

### 1. Principle of Least Privilege

Grant users the minimum permissions needed:

```python
# ❌ BAD: Overly permissive
@require_role(["admin", "teacher", "student"])

# ✅ GOOD: Minimal necessary permission
@require_permission("content:read:organization")
```

### 2. Use Specific Permissions

Prefer specific permissions over broad role checks:

```python
# ❌ BAD: Role check doesn't express intent
@require_role(["teacher"])
async def update_class(class_id: int, ...):
    pass

# ✅ GOOD: Permission clearly states requirement
@require_permission("class:update:own")
async def update_class(class_id: int, ...):
    pass
```

### 3. Use `@require_resource_access` for Ownership

Let the decorator handle ownership validation:

```python
# ❌ BAD: Manual ownership checking
@require_permission("content:update:organization")
async def update_content(content_id: int, user: User, db: Session):
    content = db.query(Content).filter_by(id=content_id).first()
    if not content:
        raise HTTPException(404)
    if content.created_by != user.id and user.role != "admin":
        raise HTTPException(403)
    # ... update logic

# ✅ GOOD: Decorator handles everything
@require_resource_access("content", "update")
async def update_content(content_id: int, user: User, db: Session):
    # Ownership already validated by decorator
    content = db.query(Content).filter_by(id=content_id).first()
    # ... update logic
```

### 4. Layer Security Checks

Use multiple decorators for defense in depth:

```python
@router.delete("/organization/content/{content_id}")
@require_teacher  # First check: Must be teacher or admin
@require_organization_access()  # Second check: Must have organization
@require_resource_access("content", "delete")  # Third check: Must own resource
async def delete_content(content_id: int, ...):
    pass
```

### 5. Document Permission Requirements

Add docstrings explaining permission requirements:

```python
@router.post("/classes")
@require_permission("class:create:organization")
async def create_class(data: ClassCreate, user: User = Depends(get_current_user)):
    """
    Create a new class within the user's organization.

    Required Permissions:
        - class:create:organization (Teacher or Admin)

    Access Rules:
        - Teachers can create classes in their organization
        - Admins can create classes in any organization
        - Students cannot create classes
    """
    pass
```

### 6. Test Permission Boundaries

Always test permission edge cases:

```python
# Test each role's access
def test_admin_can_delete_any_content(mock_admin):
    assert can_access(mock_admin, "content:delete:all")

def test_teacher_can_only_delete_own_content(mock_teacher):
    assert can_access(mock_teacher, "content:delete:own")
    assert not can_access(mock_teacher, "content:delete:all")

def test_student_cannot_delete_content(mock_student):
    assert not can_access(mock_student, "content:delete:own")
```

### 7. Use Middleware for Global Protection

Enable middleware for automatic protection of all endpoints:

```python
# main.py
app = FastAPI()
app.add_middleware(RBACMiddleware)

# Now all endpoints have automatic permission checking
# Individual decorators add additional specific checks
```

### 8. Organization Isolation

Always scope queries by organization for multi-tenant isolation:

```python
@router.get("/content")
@require_permission("content:read:organization")
async def list_content(
    user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id),
    db: Session = Depends(get_session)
):
    # Filter by organization
    content = db.query(Content).filter(
        Content.organization_id == org_id
    ).all()
    return content
```

### 9. Cache Permission Checks

For frequently accessed permissions, use the built-in cache:

```python
# RBACManager automatically caches role permissions
# First call: Computes and caches
perms = rbac_manager.get_role_permissions(Role.TEACHER)

# Subsequent calls: Uses cache (fast)
perms = rbac_manager.get_role_permissions(Role.TEACHER)
```

### 10. Monitor Audit Logs

Regularly review RBAC audit logs for security monitoring:

```bash
# Search for denied access attempts
grep "RBAC DENIED" app.log | tail -100

# Find users hitting permission errors
grep "RBAC DENIED" app.log | grep "user=123"

# Monitor permission usage
grep "RBAC GRANTED" app.log | awk '{print $5}' | sort | uniq -c
```

---

## Migration Guide

### Migrating Existing Endpoints

#### Before: Basic Role Checking

```python
from apps.backend.core.deps import require_teacher

@router.post("/content")
async def create_content(user: User = Depends(require_teacher)):
    # Simple role check only
    pass
```

#### After: RBAC with Permissions

```python
from apps.backend.core.security.rbac_decorators import require_permission

@router.post("/content")
@require_permission("content:create:organization")
async def create_content(user: User = Depends(get_current_user)):
    # Permission-based with organization scope
    pass
```

### Step-by-Step Migration

**1. Identify Current Access Control:**

```bash
# Find all endpoints with role checks
grep -r "require_admin\|require_teacher\|require_student" apps/backend/api/
```

**2. Map Roles to Permissions:**

| Current Check | New Permission |
|--------------|----------------|
| `require_admin` | Use `require_admin` (already RBAC-aware) |
| `require_teacher` | Use `require_teacher` or specific permission |
| `require_student` | Use `require_teacher_or_student` or permission |
| Manual role check | Replace with `@require_permission()` |

**3. Update Endpoint:**

```python
# OLD
@router.delete("/content/{content_id}")
async def delete_content(
    content_id: int,
    user: User = Depends(require_teacher)
):
    content = db.query(Content).filter_by(id=content_id).first()
    if content.created_by != user.id:
        raise HTTPException(403, "Not your content")
    # ... delete logic

# NEW
@router.delete("/content/{content_id}")
@require_resource_access("content", "delete")
async def delete_content(
    content_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    # Ownership check handled by decorator
    content = db.query(Content).filter_by(id=content_id).first()
    # ... delete logic
```

**4. Add Tests:**

```python
# Test the new permission-based endpoint
def test_delete_content_requires_ownership(mock_teacher, mock_db):
    # Teacher can delete their own content
    result = delete_content(
        content_id=1,
        user=mock_teacher,
        db=mock_db
    )
    assert result.status_code == 200

    # Teacher cannot delete other's content
    with pytest.raises(HTTPException):
        delete_content(
            content_id=999,  # Not owned by teacher
            user=mock_teacher,
            db=mock_db
        )
```

**5. Deploy Incrementally:**

- Migrate one router at a time
- Run tests after each migration
- Monitor logs for permission denials
- Adjust permissions as needed

### Backward Compatibility

Old role-checking functions remain available:

```python
# These still work (internally use RBAC)
from apps.backend.core.deps import (
    require_admin,
    require_teacher,
    require_student
)

# But new code should use RBAC decorators
from apps.backend.core.security.rbac_decorators import (
    require_admin,
    require_teacher,
    require_permission
)
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied (403) for Valid Users

**Symptom:** User with correct role gets 403 Forbidden

**Cause:** Permission scope doesn't match

**Solution:** Check permission scope:

```python
# If teacher gets 403 on content creation:
# Check if decorator requires :all scope
@require_permission("content:create:all")  # ❌ Teacher doesn't have :all

# Should be:
@require_permission("content:create:organization")  # ✅ Teacher has :organization
```

#### 2. Resource Not Found (404) with Valid ID

**Symptom:** Resource exists but returns 404

**Cause:** Resource in different organization

**Solution:** Add organization to query:

```python
# ❌ BAD: No organization filter
content = db.query(Content).filter_by(id=content_id).first()

# ✅ GOOD: Filter by organization
content = db.query(Content).filter(
    Content.id == content_id,
    Content.organization_id == user.organization_id
).first()
```

#### 3. Decorator Order Issues

**Symptom:** Unexpected 401 or missing attributes

**Cause:** Wrong decorator order

**Solution:** Remember decorators execute bottom-to-top:

```python
# ❌ BAD: Organization check before user extraction
@require_organization_access()
@require_permission("content:create:organization")
async def create_content(user: User = Depends(get_current_user)):
    pass

# ✅ GOOD: Permission check provides user first
@require_permission("content:create:organization")
@require_organization_access()
async def create_content(user: User = Depends(get_current_user)):
    pass
```

#### 4. Middleware Blocking Everything

**Symptom:** All requests return 401/403

**Cause:** Middleware enabled but users not set in request state

**Solution:** Ensure authentication middleware runs first:

```python
# main.py
app.add_middleware(AuthenticationMiddleware)  # Must be first
app.add_middleware(RBACMiddleware)  # Runs after auth
```

#### 5. Resource Access Decorator Not Working

**Symptom:** `@require_resource_access` returns 500 or doesn't check ownership

**Cause:** Path parameter naming mismatch

**Solution:** Path parameter must be named `{resource_type}_id`:

```python
# ❌ BAD: Parameter name doesn't match
@router.delete("/content/{id}")
@require_resource_access("content", "delete")
async def delete_content(id: int, ...):  # Should be content_id
    pass

# ✅ GOOD: Correct naming
@router.delete("/content/{content_id}")
@require_resource_access("content", "delete")
async def delete_content(content_id: int, ...):  # Matches resource type
    pass
```

### Debugging Tips

#### Enable Debug Logging

```python
import logging

# Enable RBAC debug logs
logging.getLogger("apps.backend.core.security").setLevel(logging.DEBUG)
```

#### Check User Permissions

```python
from apps.backend.core.security.rbac_manager import rbac_manager

# Get all permissions for user
perms = rbac_manager.get_user_permissions(user)
print(f"User permissions: {perms}")

# Check specific permission
has_perm = rbac_manager.has_permission(user, "content:create:organization")
print(f"Has permission: {has_perm}")

# Check access scope
scope = rbac_manager.get_accessible_resources(user, "content", "read")
print(f"Access scope: {scope}")
```

#### Test Permission Logic Directly

```python
# Test in Python shell
from apps.backend.core.security.rbac_manager import rbac_manager, Role

class MockUser:
    def __init__(self, role):
        self.id = 1
        self.role = role
        self.organization_id = uuid4()

user = MockUser(Role.TEACHER)
print(rbac_manager.has_permission(user, "content:create:organization"))
# Should print: True
```

#### Review Audit Logs

```bash
# Find all access attempts for user
grep "user=123" logs/app.log | grep RBAC

# Find all denials for specific endpoint
grep "RBAC DENIED" logs/app.log | grep "/api/v1/content"

# Check permission being checked
grep "RBAC" logs/app.log | grep "content:create"
```

### Getting Help

If you encounter issues not covered here:

1. **Check Tests:** Look at `tests/unit/core/security/` for examples
2. **Read Code:** RBAC managers have extensive docstrings
3. **Review Logs:** Enable debug logging for detailed information
4. **Ask Team:** Contact the security team or architecture team

---

## Appendix

### Complete Role Permissions Reference

See the [Role Permissions Matrix](#role-permissions-matrix) section for a complete table.

### Permission Naming Conventions

- Use lowercase for all parts
- Use colons to separate parts
- Format: `resource:action:scope`
- Examples:
  - `content:create:organization`
  - `user:update:own`
  - `system:manage`

### Resource Model Requirements

For `@require_resource_access` to work, models must have:

```python
class YourModel(Base):
    id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey("users.id"))  # For :own scope
    organization_id = Column(UUID, ForeignKey("organizations.id"))  # For :organization scope
```

### API Reference

Full API documentation available in source code:
- `apps/backend/core/security/rbac_manager.py`
- `apps/backend/core/security/rbac_decorators.py`
- `apps/backend/core/security/rbac_middleware.py`

---

**Document Version:** 1.0
**Last Updated:** 2025-10-11
**Status:** Production Ready

For questions or contributions, contact the ToolboxAI security team.
