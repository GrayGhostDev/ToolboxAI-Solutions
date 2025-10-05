# Testing Week 1-2 Executor Agent Tasks

**Agent Role**: Testing Specialist - Execute Days 4-11 of comprehensive testing plan
**Worktree**: parallel-worktrees/testing-week1-2
**Branch**: feature/testing-unit-quality
**Port**: 8033
**Priority**: 🔴 CRITICAL
**Duration**: 8 developer days (Days 4-11)
**Phase**: Phase 2 - Testing & Quality (Part 1)

---

## 🎯 Mission

Execute the first 8 days of the 15-day testing plan, focusing on unit tests (500+), generic exception handling fixes (100+), and multi-tenancy completion (30% remaining). This establishes the foundation for achieving 80%+ test coverage.

---

## 📊 Current State (After Phase 1)

### Test Coverage Baseline
- **Backend**: ~60% coverage
- **Dashboard**: ~45% coverage
- **API Endpoints**: ~70% coverage
- **Critical Paths**: ~80% coverage

### Test Infrastructure
- React 19.1.0 test utilities ✅
- Mantine provider integration ✅
- Pusher mock ✅
- TestProviders wrapper ✅
- pytest configuration ✅

### Code Quality Issues
- **Generic Exceptions**: 1,811 handlers (target: <1,000 after this phase)
- **Multi-tenancy**: 70% complete (target: 100%)
- **TODOs/FIXMEs**: 70 unresolved

---

## 🧪 Week 1: Unit Tests (Days 4-8) - 500+ Tests

### Day 4-5: User Authentication & Authorization (100 tests)
**Estimated Time**: 2 days
**Target Coverage**: User/Auth/Role modules → 85%+

#### Task 4.1: User Management Tests (40 tests)
**File**: `tests/unit/api/v1/test_users.py`

```python
# tests/unit/api/v1/test_users.py
import pytest
from fastapi.testclient import TestClient
from apps.backend.main import app

client = TestClient(app)

class TestUserEndpoints:
    """Test user management endpoints"""

    def test_get_current_user_authenticated(self, auth_headers):
        """Test retrieving current user profile"""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert "email" in response.json()
        assert "id" in response.json()

    def test_get_current_user_unauthenticated(self):
        """Test 401 without auth"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_update_user_profile(self, auth_headers, test_user):
        """Test updating user profile"""
        update_data = {
            "display_name": "Updated Name",
            "bio": "New bio text"
        }
        response = client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "Updated Name"

    def test_update_user_unauthorized(self, auth_headers):
        """Test cannot update other user's profile"""
        response = client.patch(
            "/api/v1/users/other-user-id",
            json={"display_name": "Hacked"},
            headers=auth_headers
        )
        assert response.status_code == 403

    def test_list_users_admin_only(self, admin_headers):
        """Test listing users requires admin role"""
        response = client.get("/api/v1/users", headers=admin_headers)
        assert response.status_code == 200
        assert "items" in response.json()

    def test_list_users_non_admin_forbidden(self, auth_headers):
        """Test non-admin cannot list users"""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == 403

    # Add 34 more user management tests:
    # - User creation (admin only)
    # - User deletion (admin only, soft delete)
    # - User search and filtering
    # - User pagination
    # - User profile image upload
    # - User preferences update
    # - User notification settings
    # - User timezone and locale
    # - User email verification
    # - User password change
    # - User account deactivation
    # - User role assignment (admin only)
    # - User permissions check
    # - User activity logging
```

#### Task 4.2: Authentication Tests (30 tests)
**File**: `tests/unit/api/v1/test_auth.py`

```python
# tests/unit/api/v1/test_auth.py
import pytest
from fastapi.testclient import TestClient

class TestAuthenticationFlow:
    """Test authentication endpoints"""

    def test_login_success(self, test_user):
        """Test successful login with valid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "username": test_user.email,
            "password": "correct_password"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()

    def test_login_invalid_credentials(self):
        """Test login fails with invalid password"""
        response = client.post("/api/v1/auth/login", json={
            "username": "user@example.com",
            "password": "wrong_password"
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_token_refresh(self, refresh_token):
        """Test refreshing access token"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_token_refresh_expired(self, expired_refresh_token):
        """Test refresh fails with expired token"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": expired_refresh_token
        })
        assert response.status_code == 401

    # Add 26 more authentication tests:
    # - JWT token validation
    # - Token expiration handling
    # - Logout (token blacklisting)
    # - Password reset request
    # - Password reset confirmation
    # - Email verification
    # - Multi-factor authentication (if enabled)
    # - OAuth2 flow (if implemented)
    # - Rate limiting on login attempts
    # - Account lockout after failed attempts
    # - Session management
    # - Token rotation
    # - CSRF protection
```

#### Task 4.3: Role-Based Access Control Tests (30 tests)
**File**: `tests/unit/core/auth/test_rbac.py`

```python
# tests/unit/core/auth/test_rbac.py
import pytest
from apps.backend.core.auth.rbac_manager import RBACManager

class TestRBACManager:
    """Test role-based access control"""

    def test_has_permission_super_admin(self):
        """Test super admin has all permissions"""
        rbac = RBACManager()
        assert rbac.has_permission("super_admin", "users:delete")
        assert rbac.has_permission("super_admin", "any:permission")

    def test_has_permission_admin(self):
        """Test admin has most permissions"""
        rbac = RBACManager()
        assert rbac.has_permission("admin", "users:create")
        assert rbac.has_permission("admin", "content:delete")
        assert not rbac.has_permission("admin", "system:config")

    def test_has_permission_teacher(self):
        """Test teacher has limited permissions"""
        rbac = RBACManager()
        assert rbac.has_permission("teacher", "content:create")
        assert rbac.has_permission("teacher", "assignments:grade")
        assert not rbac.has_permission("teacher", "users:delete")

    def test_has_permission_student(self):
        """Test student has minimal permissions"""
        rbac = RBACManager()
        assert rbac.has_permission("student", "content:read")
        assert rbac.has_permission("student", "assignments:submit")
        assert not rbac.has_permission("student", "content:create")

    # Add 26 more RBAC tests:
    # - Role hierarchy (admin includes teacher permissions)
    # - Permission scopes (own, team, all)
    # - Dynamic permission assignment
    # - Permission caching
    # - Permission revocation
    # - Role assignment to users
    # - Multiple roles per user
    # - Permission wildcards
    # - Resource-based permissions
    # - Time-based permissions
```

**Day 4-5 Success Criteria**:
- [ ] 100 tests written for user/auth/role modules
- [ ] Coverage: User module → 85%+, Auth module → 90%+, RBAC module → 95%+
- [ ] All tests passing
- [ ] Committed to feature/testing-unit-quality branch

---

### Day 6: Content Management (150 tests)
**Estimated Time**: 1 day
**Target Coverage**: Content module → 85%+

#### Task 6.1: Content CRUD Tests (60 tests)
**File**: `tests/unit/api/v1/test_content.py`

```python
# tests/unit/api/v1/test_content.py
class TestContentEndpoints:
    """Test content management endpoints"""

    def test_create_content_authenticated(self, auth_headers):
        """Test creating content with valid data"""
        content_data = {
            "title": "Test Content",
            "description": "Test description",
            "content_type": "lesson",
            "status": "draft"
        }
        response = client.post(
            "/api/v1/content",
            json=content_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Content"

    def test_get_content_by_id(self, test_content, auth_headers):
        """Test retrieving content by ID"""
        response = client.get(
            f"/api/v1/content/{test_content.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_content.id)

    def test_update_content(self, test_content, auth_headers):
        """Test updating content"""
        update_data = {"title": "Updated Title"}
        response = client.patch(
            f"/api/v1/content/{test_content.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_delete_content(self, test_content, admin_headers):
        """Test soft-deleting content (admin only)"""
        response = client.delete(
            f"/api/v1/content/{test_content.id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    # Add 56 more content tests:
    # - Content list with pagination
    # - Content filtering (by type, status, author)
    # - Content search
    # - Content categories
    # - Content tags
    # - Content versioning
    # - Content publish/unpublish
    # - Content scheduling
    # - Content permissions
    # - Content sharing
    # - Content analytics
    # - Content duplication
    # - Bulk content operations
```

#### Task 6.2: Content Generation Tests (50 tests)
**File**: `tests/unit/services/test_content_service.py`

```python
# tests/unit/services/test_content_service.py
class TestContentService:
    """Test AI content generation service"""

    @pytest.mark.asyncio
    async def test_generate_content_success(self):
        """Test successful content generation"""
        service = ContentService()
        result = await service.generate_content({
            "prompt": "Create a math lesson",
            "grade_level": "5th",
            "subject": "mathematics"
        })
        assert result["status"] == "completed"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_generate_content_with_templates(self):
        """Test content generation with templates"""
        service = ContentService()
        result = await service.generate_content({
            "template": "lesson_plan",
            "topic": "Fractions"
        })
        assert "learning_objectives" in result["content"]
        assert "activities" in result["content"]

    # Add 48 more content generation tests:
    # - Different content types (lesson, quiz, worksheet)
    # - Template validation
    # - Content quality checks
    # - Content moderation
    # - Error handling for API failures
    # - Caching of generated content
    # - Content regeneration
    # - Custom prompt handling
```

#### Task 6.3: Content Analytics Tests (40 tests)
**File**: `tests/unit/services/test_analytics.py`

```python
# tests/unit/services/test_analytics.py
class TestAnalyticsService:
    """Test analytics and reporting"""

    def test_track_content_view(self, test_content, test_user):
        """Test tracking content views"""
        analytics = AnalyticsService()
        analytics.track_view(content_id=test_content.id, user_id=test_user.id)

        stats = analytics.get_content_stats(test_content.id)
        assert stats["views"] >= 1

    def test_track_content_completion(self, test_content, test_user):
        """Test tracking content completion"""
        analytics = AnalyticsService()
        analytics.track_completion(
            content_id=test_content.id,
            user_id=test_user.id,
            score=85
        )

        stats = analytics.get_user_progress(test_user.id)
        assert test_content.id in stats["completed"]

    # Add 38 more analytics tests:
    # - Engagement metrics
    # - Time-on-content tracking
    # - Progress tracking
    # - Performance analytics
    # - Cohort analysis
    # - Retention metrics
    # - A/B test tracking
```

**Day 6 Success Criteria**:
- [ ] 150 tests written for content management
- [ ] Coverage: Content API → 85%+, Content Service → 80%+, Analytics → 75%+
- [ ] All tests passing
- [ ] Committed to branch

---

### Day 7: Roblox Integration (140 tests)
**Estimated Time**: 1 day
**Target Coverage**: Roblox module → 85%+

#### Task 7.1: Roblox API Tests (50 tests)
**File**: `tests/unit/api/v1/test_roblox.py`

```python
# tests/unit/api/v1/test_roblox.py
class TestRobloxEndpoints:
    """Test Roblox integration endpoints"""

    def test_get_game_info(self, test_game_id, auth_headers):
        """Test retrieving game information"""
        response = client.get(
            f"/api/v1/roblox/games/{test_game_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "name" in response.json()
        assert "description" in response.json()

    def test_deploy_script(self, test_script, admin_headers):
        """Test deploying script to Roblox"""
        response = client.post(
            "/api/v1/roblox/deploy",
            json={
                "script_id": test_script.id,
                "game_id": "test-game-id"
            },
            headers=admin_headers
        )
        assert response.status_code == 202  # Async deployment
        assert "deployment_id" in response.json()

    # Add 48 more Roblox API tests:
    # - Game list and search
    # - Asset upload
    # - Asset update
    # - Deployment status check
    # - Deployment rollback
    # - Game analytics
    # - Player data sync
    # - Leaderboard sync
```

#### Task 7.2: Roblox Deployment Tests (50 tests)
**File**: `tests/unit/services/test_roblox_deployment.py`

```python
# tests/unit/services/test_roblox_deployment.py
class TestRobloxDeploymentService:
    """Test Roblox deployment service"""

    @pytest.mark.asyncio
    async def test_deploy_asset(self):
        """Test asset deployment"""
        service = RobloxDeploymentService()
        result = await service.deploy_asset({
            "asset_type": "script",
            "content": "-- Lua script content",
            "target": "game-id"
        })
        assert result["status"] == "deployed"
        assert "asset_id" in result

    @pytest.mark.asyncio
    async def test_deploy_with_versioning(self):
        """Test deployment with version control"""
        service = RobloxDeploymentService()
        result = await service.deploy_with_version({
            "asset_id": "existing-asset",
            "version": "1.2.0",
            "changes": "Bug fixes"
        })
        assert result["version"] == "1.2.0"

    # Add 48 more deployment tests:
    # - Deployment validation
    # - Rollback functionality
    # - Version history
    # - Asset bundling
    # - Compression
    # - SHA-256 verification
    # - Rate limiting compliance
    # - Circuit breakers
```

#### Task 7.3: Roblox Sync Tests (40 tests)
**File**: `tests/unit/services/test_roblox_sync.py`

```python
# tests/unit/services/test_roblox_sync.py
class TestRobloxSyncService:
    """Test Roblox data synchronization"""

    @pytest.mark.asyncio
    async def test_sync_player_data(self):
        """Test syncing player data from Roblox"""
        service = RobloxSyncService()
        result = await service.sync_player_data("player-id")
        assert "username" in result
        assert "stats" in result

    # Add 39 more sync tests:
    # - Leaderboard sync
    # - Achievement sync
    # - Inventory sync
    # - Real-time data updates
    # - Conflict resolution
    # - Data transformation
```

**Day 7 Success Criteria**:
- [ ] 140 tests written for Roblox integration
- [ ] Coverage: Roblox API → 85%+, Deployment → 80%+, Sync → 75%+
- [ ] All tests passing
- [ ] Committed to branch

---

### Day 8: Analytics & Payment (110 tests)
**Estimated Time**: 1 day
**Target Coverage**: Analytics/Payment modules → 85%+

#### Task 8.1: Analytics Tests (40 tests)
**File**: `tests/unit/api/v1/test_analytics.py`

```python
# tests/unit/api/v1/test_analytics.py
class TestAnalyticsEndpoints:
    """Test analytics endpoints"""

    def test_get_dashboard_stats(self, admin_headers):
        """Test retrieving dashboard statistics"""
        response = client.get(
            "/api/v1/analytics/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "active_users" in response.json()
        assert "total_content" in response.json()

    # Add 39 more analytics tests:
    # - User engagement metrics
    # - Content performance
    # - Cohort analysis
    # - Custom reports
    # - Data export
```

#### Task 8.2: Payment Tests (40 tests)
**File**: `tests/unit/services/test_stripe_service.py`

```python
# tests/unit/services/test_stripe_service.py
class TestStripeService:
    """Test Stripe payment service"""

    @pytest.mark.asyncio
    async def test_create_payment_intent(self):
        """Test creating payment intent"""
        service = StripeService()
        result = await service.create_payment_intent({
            "amount": 1000,  # $10.00
            "currency": "usd",
            "customer_id": "cus_test"
        })
        assert result["status"] == "requires_payment_method"

    # Add 39 more payment tests:
    # - Subscription management
    # - Invoice generation
    # - Payment method handling
    # - Refund processing
    # - Webhook handling
    # - Dunning management
```

#### Task 8.3: Email Tests (30 tests)
**File**: `tests/unit/services/test_email_service.py`

```python
# tests/unit/services/test_email_service.py
class TestEmailService:
    """Test email service"""

    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        """Test sending welcome email"""
        service = EmailService()
        result = await service.send_welcome_email({
            "to": "user@example.com",
            "name": "Test User"
        })
        assert result["status"] == "sent"

    # Add 29 more email tests:
    # - Template rendering
    # - Queue management
    # - Retry logic
    # - Bounce handling
    # - Unsubscribe handling
```

**Day 8 Success Criteria**:
- [ ] 110 tests written for analytics/payment/email
- [ ] Coverage: Analytics → 80%+, Payment → 85%+, Email → 85%+
- [ ] All tests passing
- [ ] Week 1 complete: 500+ unit tests written

---

## 🔧 Week 2: Code Quality & Features (Days 9-11)

### Day 9: Fix Generic Exception Handlers (100+)
**Estimated Time**: 1 day
**Goal**: Reduce from 1,811 to <1,000 generic handlers

#### Task 9.1: Create Custom Exception Hierarchy
**File**: `apps/backend/core/exceptions.py`

```python
# apps/backend/core/exceptions.py

class ToolboxAIException(Exception):
    """Base exception for all ToolboxAI errors"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self):
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Authentication Exceptions
class AuthenticationError(ToolboxAIException):
    """Base authentication error"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""
    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    pass


class TokenInvalidError(AuthenticationError):
    """JWT token is invalid"""
    pass


# Authorization Exceptions
class AuthorizationError(ToolboxAIException):
    """Base authorization error"""
    pass


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""
    pass


class ResourceAccessDeniedError(AuthorizationError):
    """Access to resource denied"""
    pass


# Content Exceptions
class ContentError(ToolboxAIException):
    """Base content error"""
    pass


class ContentNotFoundError(ContentError):
    """Content not found"""
    pass


class ContentValidationError(ContentError):
    """Content validation failed"""
    pass


class ContentGenerationError(ContentError):
    """AI content generation failed"""
    pass


# Storage Exceptions
class StorageError(ToolboxAIException):
    """Base storage error"""
    pass


class FileSizeExceededError(StorageError):
    """File exceeds size limit"""
    pass


class FileTypeNotAllowedError(StorageError):
    """File type not allowed"""
    pass


class StorageQuotaExceededError(StorageError):
    """Storage quota exceeded"""
    pass


# External Service Exceptions
class ExternalServiceError(ToolboxAIException):
    """Base external service error"""
    pass


class StripeError(ExternalServiceError):
    """Stripe API error"""
    pass


class SendGridError(ExternalServiceError):
    """SendGrid API error"""
    pass


class RobloxAPIError(ExternalServiceError):
    """Roblox API error"""
    pass


class PusherError(ExternalServiceError):
    """Pusher API error"""
    pass


# Database Exceptions
class DatabaseError(ToolboxAIException):
    """Base database error"""
    pass


class RecordNotFoundError(DatabaseError):
    """Database record not found"""
    pass


class UniqueConstraintViolationError(DatabaseError):
    """Unique constraint violated"""
    pass


# Tenant Exceptions
class TenantError(ToolboxAIException):
    """Base tenant error"""
    pass


class TenantNotFoundError(TenantError):
    """Tenant not found"""
    pass


class TenantAccessDeniedError(TenantError):
    """Access to tenant resource denied"""
    pass
```

#### Task 9.2: Replace 100 Most Critical Generic Handlers

**Priority Files**:
1. `apps/backend/main.py` - 47 generic exceptions
2. `core/agents/orchestrator.py` - 89 generic exceptions
3. `apps/backend/services/pusher_handler.py` - 23 generic exceptions
4. `apps/backend/services/stripe_service.py` - 15 generic exceptions
5. `apps/backend/services/email_service.py` - 12 generic exceptions

**Pattern to Replace**:
```python
# BEFORE (generic):
try:
    result = await some_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")

# AFTER (specific):
try:
    result = await some_operation()
except StripeError as e:
    logger.error(f"Stripe payment failed: {e}", extra={"error_code": e.error_code})
    raise HTTPException(
        status_code=402,
        detail={"error_code": "PAYMENT_FAILED", "message": str(e)}
    )
except ExternalServiceError as e:
    logger.error(f"External service error: {e}")
    raise HTTPException(status_code=503, detail="Service temporarily unavailable")
except ToolboxAIException as e:
    logger.error(f"Application error: {e}")
    raise HTTPException(status_code=400, detail=e.to_dict())
except Exception as e:
    # Only catch truly unexpected errors
    logger.exception(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Steps**:
1. Find top 100 generic handlers: `grep -r "except Exception" apps/backend/ | head -100`
2. For each handler:
   - Identify specific exception types that could be thrown
   - Replace with specific exception handling
   - Add appropriate error logging
   - Add error codes for client
3. Test error scenarios to verify proper handling

**Day 9 Success Criteria**:
- [ ] Custom exception hierarchy created
- [ ] 100+ generic handlers replaced with specific types
- [ ] Generic exception count: 1,811 → <1,700
- [ ] All tests passing with new exception types
- [ ] Error responses include proper error codes

---

### Day 10: Complete Multi-tenancy (30% remaining)
**Estimated Time**: 1 day
**Goal**: Multi-tenancy 70% → 100%

#### Task 10.1: Implement Tenant Middleware
**File**: `apps/backend/middleware/tenant_middleware.py`

```python
# apps/backend/middleware/tenant_middleware.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from apps.backend.core.exceptions import TenantNotFoundError, TenantAccessDeniedError
import logging

logger = logging.getLogger(__name__)


class TenantContext:
    """Tenant context for request"""

    def __init__(
        self,
        tenant_id: str = None,
        organization_id: str = None,
        user_id: str = None,
        is_super_admin: bool = False,
        permissions: dict = None
    ):
        self.tenant_id = tenant_id
        self.organization_id = organization_id
        self.user_id = user_id
        self.is_super_admin = is_super_admin
        self.permissions = permissions or {}

    @property
    def effective_tenant_id(self) -> str:
        """Get effective tenant ID (org > tenant)"""
        return self.organization_id or self.tenant_id

    @property
    def has_tenant(self) -> bool:
        """Check if tenant context exists"""
        return bool(self.effective_tenant_id)

    def can_access_tenant(self, tenant_id: str) -> bool:
        """Check if context can access specified tenant"""
        if self.is_super_admin:
            return True
        return self.effective_tenant_id == tenant_id


class TenantMiddleware(BaseHTTPMiddleware):
    """Extract and validate tenant context from requests"""

    async def dispatch(self, request: Request, call_next):
        # Extract tenant from JWT token
        tenant_context = await self.extract_tenant_context(request)

        # Store in request state
        request.state.tenant_context = tenant_context

        # Process request
        response = await call_next(request)

        return response

    async def extract_tenant_context(self, request: Request) -> TenantContext:
        """Extract tenant context from JWT token"""
        # Get JWT token from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            # No auth, return empty context
            return TenantContext()

        try:
            # Decode JWT and extract tenant info
            from apps.backend.core.auth.jwt_manager import JWTManager

            jwt_manager = JWTManager()
            token = auth_header.replace("Bearer ", "")
            payload = await jwt_manager.decode_token(token)

            return TenantContext(
                tenant_id=payload.get("tenant_id"),
                organization_id=payload.get("organization_id"),
                user_id=payload.get("user_id"),
                is_super_admin=payload.get("is_super_admin", False),
                permissions=payload.get("permissions", {})
            )

        except Exception as e:
            logger.warning(f"Failed to extract tenant context: {e}")
            return TenantContext()


def get_tenant_context(request: Request) -> TenantContext:
    """Dependency to get tenant context from request"""
    if not hasattr(request.state, "tenant_context"):
        return TenantContext()
    return request.state.tenant_context


def require_tenant_context(request: Request) -> TenantContext:
    """Dependency that requires tenant context (raises 403 if missing)"""
    context = get_tenant_context(request)
    if not context.has_tenant:
        raise TenantAccessDeniedError("Tenant context required")
    return context


def validate_tenant_access(
    resource_tenant_id: str,
    context: TenantContext
) -> bool:
    """Validate that context can access resource tenant"""
    if context.is_super_admin:
        return True

    if not context.has_tenant:
        raise TenantAccessDeniedError("No tenant context available")

    if context.effective_tenant_id != resource_tenant_id:
        raise TenantAccessDeniedError(
            f"Cannot access resource from tenant {resource_tenant_id}"
        )

    return True
```

#### Task 10.2: Add Tenant-Scoped API Endpoints
**File**: `apps/backend/api/v1/endpoints/tenant_admin.py`

```python
# apps/backend/api/v1/endpoints/tenant_admin.py

from fastapi import APIRouter, Depends, HTTPException
from apps.backend.middleware.tenant_middleware import (
    get_tenant_context,
    require_tenant_context,
    TenantContext
)
from apps.backend.core.auth.rbac_manager import require_permissions

router = APIRouter(prefix="/tenants", tags=["tenant-admin"])


@router.get("/me")
async def get_current_tenant(
    context: TenantContext = Depends(require_tenant_context)
):
    """Get current tenant information"""
    tenant = await get_tenant_by_id(context.effective_tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "id": tenant.id,
        "name": tenant.name,
        "status": tenant.status,
        "settings": tenant.settings
    }


@router.patch("/me/settings")
async def update_tenant_settings(
    settings: dict,
    context: TenantContext = Depends(require_tenant_context),
    _: None = Depends(require_permissions("tenant:update"))
):
    """Update tenant settings"""
    tenant = await update_tenant(context.effective_tenant_id, settings)
    return tenant


@router.get("/usage")
async def get_tenant_usage(
    context: TenantContext = Depends(require_tenant_context)
):
    """Get tenant usage statistics"""
    usage = await get_usage_stats(context.effective_tenant_id)
    return {
        "storage_used": usage.storage_bytes,
        "storage_limit": usage.storage_limit_bytes,
        "api_calls_this_month": usage.api_calls,
        "api_call_limit": usage.api_call_limit
    }
```

#### Task 10.3: Write Tenant Tests (30 tests)
**File**: `tests/unit/middleware/test_tenant_middleware.py`

```python
# tests/unit/middleware/test_tenant_middleware.py

class TestTenantMiddleware:
    """Test tenant middleware"""

    def test_extract_tenant_from_jwt(self, tenant_jwt_token):
        """Test extracting tenant from JWT"""
        response = client.get(
            "/api/v1/content",
            headers={"Authorization": f"Bearer {tenant_jwt_token}"}
        )
        # Verify tenant context extracted
        # Verify only tenant's content returned

    def test_tenant_isolation(self, tenant1_token, tenant2_token):
        """Test tenants cannot access each other's data"""
        # Create content in tenant 1
        response1 = client.post(
            "/api/v1/content",
            json={"title": "Tenant 1 Content"},
            headers={"Authorization": f"Bearer {tenant1_token}"}
        )
        content_id = response1.json()["id"]

        # Try to access from tenant 2 (should fail)
        response2 = client.get(
            f"/api/v1/content/{content_id}",
            headers={"Authorization": f"Bearer {tenant2_token}"}
        )
        assert response2.status_code == 403

    # Add 28 more tenant tests:
    # - Super admin cross-tenant access
    # - Tenant switching
    # - Tenant usage limits
    # - Tenant settings management
```

**Day 10 Success Criteria**:
- [ ] Tenant middleware implemented and registered
- [ ] Tenant admin endpoints created
- [ ] 30 tenant tests written and passing
- [ ] Multi-tenancy 100% functional
- [ ] Tenant isolation verified

---

### Day 11: Performance Optimization Prep
**Estimated Time**: 1 day
**Goal**: Identify and document performance issues for Agent 4

#### Task 11.1: Identify N+1 Query Patterns
**Script**: `scripts/analysis/find_n_plus_1_queries.py`

```python
# scripts/analysis/find_n_plus_1_queries.py

import re
from pathlib import Path

def find_n_plus_1_patterns():
    """Find potential N+1 query patterns in codebase"""

    patterns = [
        r'for.*in.*:.*select\(',  # Loop with select inside
        r'\.all\(\).*for.*in',     # .all() followed by loop
        r'for.*items.*:.*db\.query',  # Query in loop
    ]

    issues = []
    backend_path = Path("apps/backend")

    for py_file in backend_path.rglob("*.py"):
        content = py_file.read_text()

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                issues.append({
                    "file": str(py_file),
                    "line": content[:match.start()].count("\n") + 1,
                    "pattern": match.group()
                })

    return issues


if __name__ == "__main__":
    issues = find_n_plus_1_patterns()
    print(f"Found {len(issues)} potential N+1 query patterns:")
    for issue in issues:
        print(f"  {issue['file']}:{issue['line']} - {issue['pattern']}")
```

#### Task 11.2: Document Slow Endpoints
**File**: `PERFORMANCE_ISSUES.md`

Create documentation of:
- Endpoints with response time >1s
- Endpoints with >10 database queries
- Endpoints without caching
- Endpoints with N+1 patterns

#### Task 11.3: Create Performance Test Suite Baseline
**File**: `tests/performance/test_api_performance.py`

```python
# tests/performance/test_api_performance.py

import pytest
import time
from fastapi.testclient import TestClient

class TestAPIPerformance:
    """Baseline performance tests"""

    def test_content_list_performance(self, auth_headers):
        """Test content list endpoint performance"""
        start = time.time()
        response = client.get("/api/v1/content", headers=auth_headers)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should be under 1 second

    # Add baseline tests for all critical endpoints
```

**Day 11 Success Criteria**:
- [ ] N+1 query patterns identified and documented
- [ ] Slow endpoints documented
- [ ] Performance test baseline established
- [ ] PERFORMANCE_ISSUES.md created for Agent 4

---

## 📈 Success Metrics (Days 4-11)

### Test Coverage Targets
- [x] Backend Coverage: 60% → 75% (500+ unit tests)
- [x] Dashboard Coverage: 45% → 55% (improved utilities)
- [x] API Endpoint Coverage: 70% → 85%
- [x] Critical Path Coverage: 80% → 90%

### Code Quality Targets
- [x] Generic Exceptions: 1,811 → <1,700 (100+ fixed)
- [x] Multi-tenancy: 70% → 100% complete
- [x] Type Coverage: Maintained at 85%+
- [x] Linting: 0 errors

### Performance Baseline
- [x] Slow endpoints documented
- [x] N+1 patterns identified
- [x] Performance tests created
- [x] Ready for Agent 4 optimization

---

## 🚨 Blockers and Risks

### Potential Issues
1. **Test Complexity**: Some tests may be difficult to write
   - **Mitigation**: Focus on happy paths first, edge cases later
2. **Exception Refactoring**: Breaking changes possible
   - **Mitigation**: Run full test suite after each batch
3. **Multi-tenancy**: Complex data isolation requirements
   - **Mitigation**: Thorough testing of tenant boundaries

### Dependencies
- Phase 1 (Integration) must be complete
- Test utilities must be available
- Test database must be properly seeded

---

## 📝 Handoff to Agent 3 (Testing Week 3)

**Completed Work**:
- 500+ unit tests covering core modules
- Custom exception hierarchy
- 100+ generic handlers replaced
- Multi-tenancy 100% functional
- Performance issues documented

**Ready for Agent 3**:
- E2E testing with Playwright
- Load testing with Locust
- Integration test scenarios
- Dashboard component tests
- Coverage verification

---

**Testing Week 1-2 Executor Agent - Mission Complete** 🎉
