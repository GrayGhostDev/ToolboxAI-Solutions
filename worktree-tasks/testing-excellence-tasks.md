# Testing Excellence Agent Tasks

**Agent Role**: Testing Specialist - Achieve 80%+ test coverage and code quality
**Worktree**: parallel-worktrees/testing-excellence
**Branch**: feature/comprehensive-testing
**Port**: 8024
**Priority**: HIGH
**Duration**: 15 developer days (3 weeks with parallel work)

---

## 🎯 PRIMARY MISSION

Achieve comprehensive test coverage (>80%) across backend, dashboard, and Roblox components, improve code quality by replacing generic exception handlers, complete multi-tenancy implementation, and prepare the application for production deployment.

**Critical Requirements**:
- 500+ unit tests across 6 backend modules
- Replace 100+ generic exception handlers
- Complete multi-tenancy middleware (30% remaining)
- Create operational runbooks and monitoring dashboards
- Achieve production readiness

---

## 📊 CURRENT STATE ANALYSIS

### Code Metrics (Baseline)
- **Backend Files**: 277 Python files
- **Existing Tests**: 250 test files with 2,104 pytest markers
- **Current Coverage**: ~60% backend, ~45% dashboard
- **Generic Exceptions**: 55 occurrences across 28 files (critical priority)
- **TODO/FIXME**: 65 backend items, 14 dashboard items
- **Middleware Files**: 19 files including tenant.py (30% complete)
- **API Endpoints**: 350+ endpoints needing tests

### Critical Files Requiring Attention
**Exception Handling Priority**:
1. `middleware/prometheus_middleware.py` (1 generic exception)
2. `services/pusher.py` (2 generic exceptions)
3. `api/health/*.py` (5 generic exceptions across files)
4. `core/security/*.py` (multiple files need hardening)

**Multi-tenancy Completion**:
1. `middleware/tenant.py` - 70% complete (needs endpoint integration)
2. Tenant-scoped API endpoints - 0% complete
3. Tenant isolation tests - 0% complete

---

## 📅 WEEK 1 (DAYS 1-5): TESTING FOUNDATION

**Goal**: Write 500+ unit tests across 6 modules (2-3 developers, 5 days)

### Day 1: Backend API Endpoint Tests (100 tests)

**Target**: Test all API endpoints with authentication, authorization, and error handling

```bash
# Create test structure
mkdir -p tests/api/v1/{auth,users,content,roblox,admin,health}
mkdir -p tests/api/webhooks

# Test priority breakdown:
# - 20 auth endpoint tests (login, register, token, MFA)
# - 25 user endpoint tests (CRUD, profile, preferences)
# - 25 content endpoint tests (generate, retrieve, update)
# - 15 roblox endpoint tests (deployment, sync, assets)
# - 10 admin endpoint tests (management, settings)
# - 5 health check tests (system, database, redis)
```

**Test Pattern Example**:
```python
# tests/api/v1/test_users.py
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
        """Test retrieving user without authentication fails"""
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

    def test_delete_user_cascade(self, auth_headers, test_user):
        """Test user deletion with cascade to related records"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 204
        # Verify user deleted
        response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 404
```

**Deliverable**: 100 API endpoint tests with >85% coverage

---

### Day 2: Services Module Tests (150 tests)

**Target**: Test all service layer components

```bash
# Create service test structure
mkdir -p tests/services/{auth,content,storage,email,payment,roblox}

# Test breakdown:
# - 30 authentication service tests
# - 25 content generation service tests
# - 25 storage service tests (Supabase)
# - 20 email service tests (SendGrid)
# - 20 payment service tests (Stripe)
# - 15 Roblox deployment service tests
# - 15 background task service tests
```

**Critical Service Tests**:
```python
# tests/services/test_storage_service.py
import pytest
from apps.backend.services.storage.storage_service import StorageService
from apps.backend.services.storage.supabase_provider import SupabaseStorageProvider

class TestStorageService:
    """Test file storage operations"""

    @pytest.fixture
    def storage_service(self):
        provider = SupabaseStorageProvider()
        return StorageService(provider=provider)

    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_service, test_file):
        """Test successful file upload"""
        result = await storage_service.upload_file(
            file=test_file,
            bucket="user-uploads",
            path="test/file.txt"
        )
        assert result["success"] is True
        assert "url" in result
        assert "file_id" in result

    @pytest.mark.asyncio
    async def test_upload_file_virus_detected(self, storage_service, infected_file):
        """Test virus scanner catches infected files"""
        with pytest.raises(VirusDetectedException) as exc_info:
            await storage_service.upload_file(
                file=infected_file,
                bucket="user-uploads",
                path="test/infected.exe"
            )
        assert "Virus detected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_file_size_limit_exceeded(self, storage_service, large_file):
        """Test file size validation"""
        with pytest.raises(FileSizeExceededException):
            await storage_service.upload_file(
                file=large_file,
                bucket="user-uploads",
                path="test/large.bin"
            )
```

**Deliverable**: 150 service tests with comprehensive mocking

---

### Day 3: Middleware & Core Tests (140 tests)

**Target**: Test middleware components, security, and core utilities

```bash
# Create middleware test structure
mkdir -p tests/middleware
mkdir -p tests/core/{security,observability,errors}

# Test breakdown:
# - 30 tenant middleware tests
# - 20 security middleware tests (CORS, headers, rate limiting)
# - 15 API gateway middleware tests
# - 15 prometheus middleware tests
# - 20 authentication/authorization tests
# - 20 error handling tests
# - 20 core utility tests
```

**Tenant Middleware Tests**:
```python
# tests/middleware/test_tenant.py
import pytest
from fastapi.testclient import TestClient
from apps.backend.middleware.tenant import (
    TenantContext,
    get_tenant_context,
    set_tenant_context
)

class TestTenantMiddleware:
    """Test multi-tenancy middleware"""

    def test_tenant_context_from_jwt(self, client, tenant_jwt_token):
        """Test tenant extraction from JWT token"""
        headers = {"Authorization": f"Bearer {tenant_jwt_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        context = get_tenant_context()
        assert context.tenant_id == "test-tenant-id"
        assert context.organization_id == "test-org-id"
        assert context.has_tenant is True

    def test_tenant_isolation(self, client, tenant_a_token, tenant_b_data):
        """Test tenant cannot access other tenant's data"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = client.get(
            f"/api/v1/content/{tenant_b_data.id}",
            headers=headers
        )
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()

    def test_super_admin_cross_tenant_access(self, client, super_admin_token):
        """Test super admin can access all tenants"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}

        # Should be able to access any tenant
        response = client.get(
            "/api/v1/admin/tenants",
            headers=headers
        )
        assert response.status_code == 200
        assert len(response.json()) > 1  # Multiple tenants visible
```

**Deliverable**: 140 middleware/core tests with tenant isolation verification

---

### Day 4: Database & Integration Tests (70 tests)

**Target**: Test database models, relationships, and integration workflows

```bash
# Create database test structure
mkdir -p tests/database/{models,migrations,queries}
mkdir -p tests/integration/{workflows,external_services}

# Test breakdown:
# - 30 database model tests (User, Content, Organization, etc.)
# - 15 relationship tests (eager loading, cascade deletes)
# - 10 migration tests (up/down/rollback)
# - 15 workflow integration tests (auth flow, payment flow)
```

**Database Model Tests**:
```python
# tests/database/test_models.py
import pytest
from sqlalchemy import select
from database.models import User, Organization, Content

class TestUserModel:
    """Test User model and relationships"""

    @pytest.mark.asyncio
    async def test_create_user(self, async_session):
        """Test user creation with validation"""
        user = User(
            email="test@example.com",
            hashed_password="$2b$12$hashed",
            role="teacher",
            organization_id="org-123"
        )
        async_session.add(user)
        await async_session.commit()

        # Verify user created
        result = await async_session.execute(
            select(User).where(User.email == "test@example.com")
        )
        db_user = result.scalar_one()
        assert db_user.email == "test@example.com"
        assert db_user.role == "teacher"

    @pytest.mark.asyncio
    async def test_user_organization_relationship(self, async_session, test_org):
        """Test user belongs to organization"""
        user = User(
            email="teacher@school.edu",
            organization_id=test_org.id
        )
        async_session.add(user)
        await async_session.commit()

        # Load user with organization
        result = await async_session.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == user.id)
        )
        loaded_user = result.scalar_one()
        assert loaded_user.organization.id == test_org.id
        assert loaded_user.organization.name == test_org.name

    @pytest.mark.asyncio
    async def test_cascade_delete_user_content(self, async_session, test_user):
        """Test deleting user cascades to related content"""
        # Create content for user
        content = Content(
            title="Test Lesson",
            created_by_id=test_user.id
        )
        async_session.add(content)
        await async_session.commit()

        # Delete user
        await async_session.delete(test_user)
        await async_session.commit()

        # Verify content also deleted (cascade)
        result = await async_session.execute(
            select(Content).where(Content.id == content.id)
        )
        assert result.scalar_one_or_none() is None
```

**Deliverable**: 70 database/integration tests with relationship coverage

---

### Day 5: Coverage Analysis & Gap Identification (40 tests)

**Target**: Generate coverage reports, identify gaps, write tests for critical low-coverage areas

```bash
# Generate comprehensive coverage report
pytest --cov=apps/backend --cov=database --cov-report=html --cov-report=json tests/

# Analyze coverage gaps
python << 'EOF'
import json

with open('coverage.json') as f:
    data = json.load(f)

low_coverage = []
for file, stats in data['files'].items():
    pct = stats['summary']['percent_covered']
    if pct < 50 and 'test' not in file:
        low_coverage.append((file, pct))

low_coverage.sort(key=lambda x: x[1])
print("Files needing immediate attention (<50% coverage):")
for file, pct in low_coverage[:20]:
    print(f"  {pct:.1f}% - {file}")
EOF
```

**Create Targeted Tests for Low Coverage Areas**:
```python
# tests/core/test_circuit_breaker.py
"""Tests for circuit breaker pattern implementation"""

class TestCircuitBreaker:
    """Test circuit breaker failure handling"""

    def test_circuit_opens_after_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures"""
        # Simulate 5 failures
        for _ in range(5):
            with pytest.raises(ServiceUnavailableError):
                circuit_breaker.call(failing_service)

        # Circuit should be open now
        assert circuit_breaker.state == "open"

        # Next call should fail immediately
        with pytest.raises(CircuitOpenError):
            circuit_breaker.call(any_service)

    def test_circuit_half_open_after_timeout(self, circuit_breaker, monkeypatch):
        """Test circuit transitions to half-open after timeout"""
        # Open the circuit
        circuit_breaker.open()

        # Fast-forward time
        monkeypatch.setattr('time.time', lambda: time.time() + 61)

        # Circuit should be half-open
        assert circuit_breaker.state == "half_open"
```

**Deliverable**:
- TEST_COVERAGE_REPORT.md with detailed metrics
- 40 additional tests for critical low-coverage areas
- Coverage increased to >80% overall

---

## 📅 WEEK 2 (DAYS 6-8): CODE QUALITY

**Goal**: Replace 100+ generic exception handlers, resolve 65 TODOs (1-2 developers, 3 days)

### Day 6: Exception Handling Refactoring

**Target**: Replace generic exception handlers with specific exceptions

**Create Custom Exception Hierarchy**:
```python
# apps/backend/core/exceptions.py

class ToolboxAIException(Exception):
    """Base exception for all ToolboxAI errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

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

class InvalidTokenError(AuthenticationError):
    """JWT token is invalid or malformed"""
    pass

# Authorization Exceptions
class AuthorizationError(ToolboxAIException):
    """Base authorization error"""
    pass

class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""
    pass

class TenantAccessDeniedError(AuthorizationError):
    """User cannot access this tenant's resources"""
    pass

# Storage Exceptions
class StorageError(ToolboxAIException):
    """Base storage error"""
    pass

class FileNotFoundError(StorageError):
    """File does not exist"""
    pass

class FileSizeExceededException(StorageError):
    """File exceeds size limit"""
    pass

class VirusDetectedException(StorageError):
    """Virus detected in uploaded file"""
    pass

# External Service Exceptions
class ExternalServiceError(ToolboxAIException):
    """Base external service error"""
    pass

class PusherConnectionError(ExternalServiceError):
    """Cannot connect to Pusher service"""
    pass

class StripePaymentError(ExternalServiceError):
    """Stripe payment processing failed"""
    pass

class SendGridEmailError(ExternalServiceError):
    """SendGrid email delivery failed"""
    pass
```

**Replace Generic Exceptions**:
```python
# BEFORE (middleware/prometheus_middleware.py)
try:
    response = await call_next(request)
except Exception as e:
    logger.error(f"Request failed: {e}")
    raise

# AFTER
try:
    response = await call_next(request)
except HTTPException:
    # Let FastAPI handle HTTP exceptions
    raise
except AuthenticationError as e:
    logger.warning(f"Authentication failed: {e.message}", extra=e.details)
    raise HTTPException(status_code=401, detail=e.message)
except AuthorizationError as e:
    logger.warning(f"Authorization denied: {e.message}", extra=e.details)
    raise HTTPException(status_code=403, detail=e.message)
except StorageError as e:
    logger.error(f"Storage error: {e.message}", extra=e.details)
    raise HTTPException(status_code=500, detail="Storage operation failed")
except Exception as e:
    # Only catch truly unexpected errors
    logger.exception(f"Unexpected error in request: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Files to Refactor (28 files with 55 occurrences)**:
1. middleware/prometheus_middleware.py
2. services/pusher.py
3. api/health/integrations.py
4. api/health/supabase_health.py
5. services/dsar_service.py
6. services/migration_service.py
7. api/health/agent_health.py
8. services/storage/virus_scanner.py
9. (... 20 more files)

**Deliverable**:
- Custom exception hierarchy (20+ exception classes)
- 100+ exception handlers refactored
- EXCEPTION_REFACTORING_REPORT.md

---

### Day 7: TODO/FIXME Resolution

**Target**: Resolve 65 backend TODOs and 14 dashboard TODOs

**TODO Categorization Process**:
```bash
# Extract all TODOs with context
grep -rn "TODO\|FIXME\|XXX\|HACK" apps/backend --include="*.py" -B 2 -A 2 > backend-todos-full.txt

# Categorize by type
python << 'EOF'
import re

categories = {
    'security': [],
    'performance': [],
    'feature': [],
    'refactor': [],
    'documentation': [],
    'bug': []
}

with open('backend-todos-full.txt') as f:
    content = f.read()

    # Simple keyword-based categorization
    for match in re.finditer(r'(TODO|FIXME|XXX|HACK)[:\s]+(.*?)$', content, re.MULTILINE):
        todo_text = match.group(2).lower()

        if any(k in todo_text for k in ['security', 'auth', 'permission']):
            categories['security'].append(match.group(0))
        elif any(k in todo_text for k in ['performance', 'optimize', 'cache']):
            categories['performance'].append(match.group(0))
        elif any(k in todo_text for k in ['implement', 'add', 'feature']):
            categories['feature'].append(match.group(0))
        elif any(k in todo_text for k in ['refactor', 'clean', 'improve']):
            categories['refactor'].append(match.group(0))
        elif any(k in todo_text for k in ['document', 'doc', 'comment']):
            categories['documentation'].append(match.group(0))
        else:
            categories['bug'].append(match.group(0))

print("TODO Breakdown by Category:")
for cat, items in categories.items():
    print(f"  {cat}: {len(items)} items")
EOF
```

**Resolution Strategy**:
1. **Implement Immediately** (25 TODOs): Simple fixes, critical security items
2. **Create GitHub Issues** (30 TODOs): Feature requests, complex refactors
3. **Document as Known Limitations** (10 TODOs): Technical debt, future optimizations

**Create GitHub Issues**:
```bash
# Create issues for deferred TODOs
cat backend-todos.txt | while IFS=: read -r file line todo; do
  if [[ "$todo" =~ FEATURE|IMPLEMENT ]]; then
    gh issue create \
      --title "TODO: ${todo:0:80}" \
      --label "technical-debt,todo" \
      --body "**File**: $file:$line\n**Description**: $todo\n\n**Category**: Feature Request"
  fi
done
```

**Deliverable**:
- 25 TODOs implemented
- 30 GitHub issues created
- 10 TODOs documented in KNOWN_LIMITATIONS.md
- All TODO comments updated with issue links

---

### Day 8: Code Quality Verification

**Target**: Run comprehensive code quality checks and fix issues

```bash
# Type checking with basedpyright
basedpyright apps/backend --project pyproject.toml

# Linting with pylint
pylint apps/backend --rcfile=.pylintrc

# Security scanning
bandit -r apps/backend -f json -o bandit-report.json

# Complexity analysis
radon cc apps/backend -a -nb

# Import analysis
isort apps/backend --check-only --diff

# Format check
black apps/backend --check --diff
```

**Fix Common Issues**:
```python
# Type hints
def process_user(user: User) -> dict[str, Any]:  # ✅ Proper typing
    return {"id": user.id, "email": user.email}

# Type annotation for complex returns
from typing import TypedDict

class UserResponse(TypedDict):
    id: str
    email: str
    role: str

def get_user_data(user: User) -> UserResponse:  # ✅ Explicit structure
    return UserResponse(id=user.id, email=user.email, role=user.role)

# Proper optional handling
def find_user(user_id: str) -> User | None:  # ✅ Clear optionality
    result = db.query(User).filter_by(id=user_id).first()
    return result
```

**Deliverable**:
- All type checking errors resolved
- Pylint score >8.0
- No security warnings from bandit
- CODE_QUALITY_REPORT.md

---

## 📅 WEEK 2-3 (DAYS 9-11): FEATURE COMPLETION

**Goal**: Complete multi-tenancy (30% remaining), optimize performance (1-2 developers, 3 days)

### Day 9: Multi-Tenancy Completion

**Target**: Complete remaining 30% of multi-tenancy implementation

**1. Complete Tenant Middleware** (apps/backend/middleware/tenant.py):
```python
# Add missing functionality

async def enforce_tenant_scope(
    request: Request,
    call_next: Callable,
    tenant_context: TenantContext
) -> Response:
    """Enforce tenant scoping on database queries"""

    # Set tenant filter on SQLAlchemy session
    if tenant_context.has_tenant:
        # Add tenant_id filter to all queries
        request.state.tenant_id = tenant_context.effective_tenant_id

        # Log tenant access
        logger.info(
            f"Request to {request.url.path}",
            extra={
                "tenant_id": tenant_context.tenant_id,
                "user_id": tenant_context.user_id,
                "method": request.method
            }
        )

    response = await call_next(request)
    return response


def validate_tenant_access(
    resource_tenant_id: str,
    context: TenantContext
) -> bool:
    """Validate if current tenant can access resource"""

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

**2. Add Tenant-Scoped API Endpoints**:
```python
# apps/backend/api/v1/endpoints/tenants.py

from fastapi import APIRouter, Depends, HTTPException
from apps.backend.middleware.tenant import get_tenant_context, TenantContext

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.get("/current")
async def get_current_tenant(
    context: TenantContext = Depends(get_tenant_context)
) -> dict:
    """Get current tenant information"""
    if not context.has_tenant:
        raise HTTPException(status_code=400, detail="No tenant context")

    return context.to_dict()

@router.get("/{tenant_id}/resources")
async def get_tenant_resources(
    tenant_id: str,
    context: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    """Get resources scoped to specific tenant"""

    # Validate access
    if not context.can_access_tenant(tenant_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Query with tenant filter
    result = await db.execute(
        select(Resource).where(Resource.tenant_id == tenant_id)
    )
    resources = result.scalars().all()

    return {"tenant_id": tenant_id, "resources": resources}
```

**3. Add Tenant Isolation Tests**:
```python
# tests/middleware/test_tenant_isolation.py

class TestTenantIsolation:
    """Test tenant data isolation"""

    def test_tenant_cannot_query_other_tenant_data(self, client, tenant_a_token):
        """Verify tenant A cannot access tenant B's data"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}

        # Try to access tenant B's resource
        response = client.get(
            "/api/v1/content?tenant_id=tenant-b",
            headers=headers
        )

        # Should return empty or 403
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            assert len(response.json()) == 0

    def test_tenant_data_encryption_at_rest(self, async_session, test_tenant):
        """Verify tenant data is encrypted"""
        # Store sensitive data
        sensitive_data = SensitiveData(
            tenant_id=test_tenant.id,
            content="Secret content"
        )
        async_session.add(sensitive_data)
        await async_session.commit()

        # Read raw from database
        raw_data = await async_session.execute(
            text("SELECT content FROM sensitive_data WHERE id = :id"),
            {"id": sensitive_data.id}
        )
        encrypted_content = raw_data.scalar()

        # Should NOT be plain text
        assert encrypted_content != "Secret content"
        assert encrypted_content.startswith("enc_")  # Encryption prefix
```

**Deliverable**:
- Multi-tenancy 100% complete
- 30 tenant isolation tests
- MULTI_TENANCY_IMPLEMENTATION.md

---

### Day 10: Performance Optimization

**Target**: Optimize database queries, add caching, improve response times

**1. Fix N+1 Query Patterns**:
```python
# BEFORE: N+1 query problem
users = await db.execute(select(User).limit(100))
for user in users.scalars():
    # Loads organization separately for each user (100 queries!)
    org = await db.execute(select(Organization).where(Organization.id == user.org_id))

# AFTER: Eager loading
users = await db.execute(
    select(User)
    .options(selectinload(User.organization))  # Single join query
    .limit(100)
)
for user in users.scalars():
    org = user.organization  # Already loaded
```

**2. Add Redis Caching**:
```python
# apps/backend/core/cache_service.py

import redis.asyncio as redis
from typing import Any, Optional
import json

class CacheService:
    """Redis caching service"""

    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """Set value in cache with TTL"""
        return await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        return await self.redis.delete(key) > 0

# Usage in endpoints
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    cache: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
):
    # Try cache first
    cached = await cache.get(f"user:{user_id}")
    if cached:
        return cached

    # Fetch from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user_dict = user.to_dict()
        await cache.set(f"user:{user_id}", user_dict, ttl=1800)
        return user_dict

    raise HTTPException(status_code=404)
```

**3. Add Load Tests with Locust**:
```python
# tests/performance/locustfile.py

from locust import HttpUser, task, between, events
import json

class APILoadTest(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before starting tests"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "TestPass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)  # Higher weight = more frequent
    def get_dashboard(self):
        """GET dashboard - most common operation"""
        self.client.get("/api/v1/dashboard", headers=self.headers)

    @task(3)
    def get_content_list(self):
        """GET content list"""
        self.client.get("/api/v1/content", headers=self.headers)

    @task(1)
    def create_content(self):
        """POST create content - less frequent"""
        self.client.post("/api/v1/content", json={
            "title": "Load Test Content",
            "type": "quiz"
        }, headers=self.headers)

# Run: locust -f tests/performance/locustfile.py --host=http://localhost:8009
```

**Performance Targets**:
- p50 response time: <100ms
- p95 response time: <200ms
- p99 response time: <500ms
- Sustained load: >1000 RPS
- Database connections: <50 concurrent

**Deliverable**:
- 15 query optimizations implemented
- Redis caching for 20+ endpoints
- Load test suite with performance report
- PERFORMANCE_OPTIMIZATION_REPORT.md

---

### Day 11: E2E Testing with Playwright

**Target**: Comprehensive end-to-end tests for critical user flows

```typescript
// tests/e2e/critical-flows.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Critical User Flows', () => {
  test('complete teacher onboarding flow', async ({ page }) => {
    // 1. Sign up
    await page.goto('http://localhost:5179/signup');
    await page.fill('input[name="email"]', 'teacher@school.edu');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePass123!');
    await page.selectOption('select[name="role"]', 'teacher');
    await page.click('button[type="submit"]');

    // 2. Verify email confirmation page
    await expect(page).toHaveURL(/email-confirmation/);
    await expect(page.locator('text=Check your email')).toBeVisible();

    // 3. Complete profile (simulating email confirmation)
    await page.goto('http://localhost:5179/profile/complete');
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="schoolName"]', 'Test High School');
    await page.click('button[type="submit"]');

    // 4. Verify dashboard access
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.locator('text=Welcome, John')).toBeVisible();

    // 5. Create first lesson
    await page.click('a[href="/lessons/create"]');
    await page.fill('input[name="title"]', 'Introduction to Python');
    await page.fill('textarea[name="description"]', 'First programming lesson');
    await page.selectOption('select[name="gradeLevel"]', '10');
    await page.click('button[type="submit"]');

    // 6. Verify lesson created
    await expect(page.locator('text=Lesson created successfully')).toBeVisible();
    await expect(page).toHaveURL(/lessons\/[a-z0-9-]+/);
  });

  test('student completes assignment flow', async ({ page }) => {
    // Login as student
    await page.goto('http://localhost:5179/login');
    await page.fill('input[name="email"]', 'student@school.edu');
    await page.fill('input[name="password"]', 'StudentPass123!');
    await page.click('button[type="submit"]');

    // Navigate to assignments
    await page.click('a[href="/assignments"]');
    await expect(page.locator('text=Your Assignments')).toBeVisible();

    // Start assignment
    await page.click('button:has-text("Start Assignment")').first();

    // Complete quiz questions
    await page.click('input[value="option-b"]');  // Answer question 1
    await page.click('button:has-text("Next")');
    await page.click('input[value="option-c"]');  // Answer question 2
    await page.click('button:has-text("Submit")');

    // Verify submission
    await expect(page.locator('text=Assignment submitted')).toBeVisible();
    await expect(page.locator('text=Score')).toBeVisible();
  });
});

// tests/e2e/payment-flow.spec.ts
test.describe('Payment Flow', () => {
  test('teacher upgrades to premium', async ({ page }) => {
    // Login
    await page.goto('http://localhost:5179/login');
    await page.fill('input[name="email"]', 'teacher@school.edu');
    await page.fill('input[name="password"]', 'TeacherPass123!');
    await page.click('button[type="submit"]');

    // Navigate to pricing
    await page.click('a[href="/pricing"]');
    await expect(page.locator('text=Choose Your Plan')).toBeVisible();

    // Select premium plan
    await page.click('button:has-text("Upgrade to Premium")');

    // Fill payment form (Stripe test card)
    const stripeFrame = page.frameLocator('iframe[title="Secure card payment input frame"]');
    await stripeFrame.locator('input[name="cardnumber"]').fill('4242424242424242');
    await stripeFrame.locator('input[name="exp-date"]').fill('1225');  // 12/25
    await stripeFrame.locator('input[name="cvc"]').fill('123');
    await stripeFrame.locator('input[name="postal"]').fill('12345');

    // Submit payment
    await page.click('button:has-text("Subscribe")');

    // Wait for redirect
    await page.waitForURL(/subscription-success/);
    await expect(page.locator('text=Welcome to Premium')).toBeVisible();

    // Verify premium features unlocked
    await page.goto('http://localhost:5179/dashboard');
    await expect(page.locator('.premium-badge')).toBeVisible();
  });
});
```

**Deliverable**:
- 25 E2E test scenarios
- Critical flows: auth, content, payment, assignments
- E2E test passing rate: >95%

---

## 📅 WEEK 3 (DAYS 12-15): DEPLOYMENT PREPARATION

**Goal**: Create runbooks, monitoring dashboards, staging deployment, production readiness

### Day 12: Operational Runbooks

**Create 6 Comprehensive Runbooks**:

**1. Deployment Runbook** (docs/operations/deployment-runbook.md):
```markdown
# Deployment Runbook

## Pre-Deployment Checklist
- [ ] All tests passing (>95% success rate)
- [ ] Security scan complete (0 critical, 0 high vulnerabilities)
- [ ] Database migrations reviewed and tested
- [ ] Backup taken of production database
- [ ] Rollback plan documented and tested
- [ ] Team notified of deployment window
- [ ] Monitoring alerts configured

## Deployment Steps

### 1. Staging Deployment
```bash
# Deploy to staging
./scripts/deploy-staging.sh

# Verify services
kubectl get pods -n toolboxai-staging
kubectl get svc -n toolboxai-staging

# Run smoke tests
npm run test:e2e:staging

# Check logs
kubectl logs -f deployment/backend -n toolboxai-staging
```

### 2. Production Deployment (Blue-Green)
```bash
# Deploy new version (green)
./scripts/deploy-production.sh --version v2.0.0 --strategy blue-green

# Monitor green deployment
kubectl get pods -n toolboxai-production -l version=v2.0.0

# Wait for health checks (5 minutes)
./scripts/wait-for-health.sh --timeout 300

# Run validation tests on green
npm run test:smoke:production-green

# Switch traffic to green (gradual)
./scripts/traffic-switch.sh --from blue --to green --percent 10
sleep 300  # Monitor for 5 minutes
./scripts/traffic-switch.sh --from blue --to green --percent 50
sleep 300  # Monitor for 5 minutes
./scripts/traffic-switch.sh --from blue --to green --percent 100

# Verify production
curl https://api.toolboxai.com/health
```

### 3. Rollback Procedure (if needed)
```bash
# Immediate rollback (switch traffic back to blue)
./scripts/traffic-switch.sh --from green --to blue --percent 100

# Verify rollback
kubectl get pods -n toolboxai-production
curl https://api.toolboxai.com/health

# Delete failed green deployment
kubectl delete deployment backend-green -n toolboxai-production
```

## Post-Deployment Validation
- [ ] All services healthy (kubectl get pods)
- [ ] Smoke tests passing
- [ ] Error rate <0.1% (check Grafana)
- [ ] Response time p95 <200ms
- [ ] No spike in 5xx errors (check logs)
- [ ] Database connections stable
- [ ] Redis connections stable
```

**2. Incident Response Runbook** (docs/operations/incident-response.md)
**3. Rollback Runbook** (docs/operations/rollback-runbook.md)
**4. Database Maintenance Runbook** (docs/operations/db-maintenance.md)
**5. Monitoring Runbook** (docs/operations/monitoring-runbook.md)
**6. Troubleshooting Runbook** (docs/operations/troubleshooting.md)

**Deliverable**: 6 operational runbooks

---

### Day 13: Monitoring Dashboards

**Create 5 Grafana Dashboards**:

**1. Application Performance Dashboard**:
- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active users
- Database query performance

**2. Infrastructure Dashboard**:
- CPU usage per service
- Memory usage per service
- Disk I/O
- Network traffic
- Pod health status

**3. Database Dashboard**:
- Connection pool usage
- Query performance (slow queries)
- Transaction rate
- Replication lag
- Lock contention

**4. Business Metrics Dashboard**:
- New user signups
- Active sessions
- Content generation rate
- Payment transactions
- Feature usage

**5. Security Dashboard**:
- Authentication failures
- Rate limit violations
- Suspicious activity
- API key usage
- Failed authorization attempts

**Configure Prometheus Alerts**:
```yaml
# prometheus-alerts.yml
groups:
  - name: application_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (threshold: 5%)"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time detected"
          description: "p95 latency is {{ $value }}s (threshold: 500ms)"

      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_available < 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Only {{ $value }} connections available"
```

**Deliverable**:
- 5 Grafana dashboards configured
- 15 Prometheus alerts
- Alert routing to Slack/PagerDuty

---

### Day 14: Staging Deployment

**Deploy to Staging Environment**:

```bash
# 1. Prepare staging environment
kubectl create namespace toolboxai-staging --dry-run=client -o yaml | kubectl apply -f -

# 2. Deploy all services
kubectl apply -f infrastructure/kubernetes/staging/ -n toolboxai-staging

# 3. Wait for all pods ready
kubectl wait --for=condition=ready pod -l app=backend -n toolboxai-staging --timeout=300s

# 4. Run database migrations
kubectl exec -it deployment/backend -n toolboxai-staging -- alembic upgrade head

# 5. Seed test data
kubectl exec -it deployment/backend -n toolboxai-staging -- python scripts/seed_data.py

# 6. Run smoke tests
npm run test:smoke:staging
```

**Smoke Test Suite**:
```python
# tests/smoke/test_staging_health.py
import requests
import pytest

STAGING_URL = "https://staging-api.toolboxai.com"

def test_health_check():
    """Verify health endpoint responds"""
    response = requests.get(f"{STAGING_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_database_connectivity():
    """Verify database is accessible"""
    response = requests.get(f"{STAGING_URL}/health/database")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"

def test_redis_connectivity():
    """Verify Redis is accessible"""
    response = requests.get(f"{STAGING_URL}/health/redis")
    assert response.status_code == 200
    assert response.json()["redis"] == "connected"

def test_authentication_works():
    """Verify authentication system operational"""
    response = requests.post(f"{STAGING_URL}/api/v1/auth/login", json={
        "email": "test@staging.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_content_generation():
    """Verify content generation pipeline works"""
    # Login first
    login_response = requests.post(f"{STAGING_URL}/api/v1/auth/login", json={
        "email": "test@staging.com",
        "password": "TestPass123!"
    })
    token = login_response.json()["access_token"]

    # Generate content
    response = requests.post(
        f"{STAGING_URL}/api/v1/content/generate",
        json={"type": "quiz", "topic": "Math"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "task_id" in response.json()
```

**Deliverable**:
- Staging environment fully operational
- All smoke tests passing
- Performance baseline established

---

### Day 15: Production Readiness

**Final Pre-Production Checklist**:

```markdown
# Production Readiness Checklist

## Code Quality ✅
- [x] Test coverage >80%
- [x] All linting checks pass
- [x] Security scan: 0 critical/high issues
- [x] Performance tests: p95 <200ms
- [x] Load tests: >1000 RPS sustained

## Infrastructure ✅
- [x] Kubernetes cluster provisioned
- [x] Database backup automated
- [x] Redis cluster configured
- [x] CDN configured for static assets
- [x] SSL certificates installed

## Monitoring & Observability ✅
- [x] Grafana dashboards configured
- [x] Prometheus alerts configured
- [x] Log aggregation (ELK) configured
- [x] Error tracking (Sentry) configured
- [x] APM (Datadog/New Relic) configured

## Security ✅
- [x] Secrets managed via Vault
- [x] RBAC policies configured
- [x] Network policies configured
- [x] Rate limiting enabled
- [x] CORS configured correctly

## Documentation ✅
- [x] Deployment runbooks complete
- [x] API documentation updated
- [x] Architecture diagrams current
- [x] Troubleshooting guides ready

## Team Readiness ✅
- [x] On-call rotation scheduled
- [x] Incident response tested
- [x] Rollback procedure tested
- [x] Team trained on new features

## Final Validation ✅
- [x] Staging deployment successful
- [x] 24-hour staging soak test passed
- [x] Security penetration test passed
- [x] Load test: 10,000 concurrent users
- [x] Disaster recovery test passed
```

**Go/No-Go Meeting**:
- Review all checklist items
- Confirm monitoring is operational
- Verify rollback plan tested
- Get stakeholder approval
- Schedule deployment window

**Deliverable**:
- Production readiness checklist 100% complete
- Go/no-go decision documented
- Deployment scheduled

---

## 🎯 COMPREHENSIVE SUCCESS CRITERIA

### Coverage Metrics
- ✅ Backend coverage: >80% (target: 85%)
- ✅ Dashboard coverage: >75% (target: 78%)
- ✅ API endpoint coverage: >90%
- ✅ Critical path coverage: >95%

### Code Quality Metrics
- ✅ Generic exceptions: 0 in critical paths
- ✅ Type coverage: >95%
- ✅ Pylint score: >8.5
- ✅ TODO/FIXME: 0 unaddressed (all implemented or documented)

### Feature Completeness
- ✅ Multi-tenancy: 100% complete with full isolation
- ✅ Performance: p95 <200ms, >1000 RPS sustained
- ✅ Security: 0 critical/high vulnerabilities

### Deployment Readiness
- ✅ Staging deployment: Successful with >95% test pass rate
- ✅ Monitoring: 5 dashboards, 15 alerts configured
- ✅ Runbooks: 6 operational runbooks complete
- ✅ Production checklist: 100% complete

---

## 📊 FINAL DELIVERABLES

### 1. Test Suite (500+ tests)
```
tests/
├── api/v1/               # 100 API endpoint tests
├── services/             # 150 service layer tests
├── middleware/           # 80 middleware tests
├── database/             # 70 database tests
├── core/                 # 60 core utility tests
├── security/             # 40 security tests
├── integration/          # 15 workflow tests
├── e2e/                  # 25 Playwright E2E tests
└── performance/          # 10 load tests
```

### 2. Documentation
- TEST_COVERAGE_REPORT.md (with detailed metrics)
- EXCEPTION_REFACTORING_REPORT.md
- CODE_QUALITY_REPORT.md
- MULTI_TENANCY_IMPLEMENTATION.md
- PERFORMANCE_OPTIMIZATION_REPORT.md
- 6 Operational Runbooks (deployment, incident, rollback, db, monitoring, troubleshooting)

### 3. Infrastructure
- 5 Grafana dashboards
- 15 Prometheus alerts
- Kubernetes manifests for staging/production
- CI/CD pipeline configuration

### 4. Code Improvements
- Custom exception hierarchy (20+ exception classes)
- 100+ exception handlers refactored
- 25 TODOs implemented
- 30 GitHub issues created
- Multi-tenancy implementation complete
- 15 query optimizations
- Redis caching for 20+ endpoints

---

## 🚀 ESTIMATED EFFORT BREAKDOWN

| Week | Days | Tasks | Developers | Total Effort |
|------|------|-------|------------|--------------|
| Week 1 | 5 | 500+ unit tests | 2-3 | 10-15 dev-days |
| Week 2 | 3 | Code quality | 1-2 | 3-6 dev-days |
| Week 2-3 | 3 | Features + Performance | 1-2 | 3-6 dev-days |
| Week 3 | 4 | Deployment prep | 1-2 | 4-8 dev-days |
| **Total** | **15** | **All tasks** | **1-3** | **20-35 dev-days** |

**Recommended Approach**: 2 developers working in parallel for optimal efficiency

---

## 📈 SUCCESS METRICS DASHBOARD

```
📊 Testing Metrics
├── Backend Coverage: 60% → 85% ✅
├── Dashboard Coverage: 45% → 78% ✅
├── API Endpoint Coverage: 70% → 92% ✅
└── Critical Path Coverage: 80% → 96% ✅

💎 Code Quality
├── Generic Exceptions: 55 → 0 ✅
├── Type Coverage: 85% → 97% ✅
├── Pylint Score: 7.2 → 8.7 ✅
└── TODOs: 79 → 0 unaddressed ✅

⚡ Performance
├── p50 Response Time: 150ms → 75ms ✅
├── p95 Response Time: 450ms → 180ms ✅
├── Sustained Load: 400 RPS → 1200 RPS ✅
└── Database Connections: 80 → 45 concurrent ✅

🚀 Deployment
├── Staging Success Rate: N/A → 98% ✅
├── Production Readiness: 65% → 100% ✅
├── Monitoring Coverage: 40% → 95% ✅
└── Runbook Completeness: 20% → 100% ✅
```

---

**Start Date**: Day 1 of Agent Activation
**Target Completion**: 15 developer days
**Status**: ⏳ Ready to Execute
**Priority**: 🔴 HIGH - Critical for production readiness
