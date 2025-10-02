# API Development & Completion Worktree Tasks
**Branch**: feature/api-endpoints-completion
**Ports**: Backend(8019), Dashboard(5190), MCP(9887), Coordinator(8898)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Read and follow `2025-IMPLEMENTATION-STANDARDS.md` before writing ANY code!

**Requirements**:
- ✅ Python 3.12 with type hints
- ✅ FastAPI async endpoints
- ✅ Pydantic v2 models with ConfigDict
- ✅ SQLAlchemy 2.0 async patterns
- ✅ Auto-accept enabled for corrections
- ❌ NO sync-only code or Pydantic v1 patterns

## Primary Objectives

### 1. **Complete Missing API Endpoints**
   - Implement upload/media endpoints for storage service
   - Add tenant admin and settings endpoints
   - Create remaining analytics endpoints
   - Build content management APIs

### 2. **API Documentation & Standards**
   - Generate comprehensive OpenAPI/Swagger docs
   - Add request/response examples
   - Create API usage guides
   - Implement API versioning strategy

### 3. **API Testing & Validation**
   - Write integration tests for all endpoints
   - Add request validation tests
   - Test authentication/authorization
   - Implement API contract testing

## Current Tasks

### Phase 1: Storage Service API Endpoints (Priority: CRITICAL)

The storage service is complete but missing API endpoints!

**Files to Create:**
- [ ] `apps/backend/api/v1/endpoints/uploads.py` - File upload endpoints
- [ ] `apps/backend/api/v1/endpoints/media.py` - Media serving endpoints
- [ ] `apps/backend/api/v1/endpoints/storage_admin.py` - Storage admin

**Upload Endpoints**:
- [ ] `POST /api/v1/uploads/file` - Single file upload
- [ ] `POST /api/v1/uploads/multipart/init` - Initialize multipart upload
- [ ] `POST /api/v1/uploads/multipart/part` - Upload part
- [ ] `POST /api/v1/uploads/multipart/complete` - Complete multipart
- [ ] `DELETE /api/v1/uploads/{file_id}` - Delete uploaded file
- [ ] `GET /api/v1/uploads/{file_id}/status` - Check upload status

**Media Endpoints**:
- [ ] `GET /api/v1/media/{file_id}` - Serve file with signed URL
- [ ] `GET /api/v1/media/{file_id}/thumbnail` - Serve thumbnail
- [ ] `GET /api/v1/media/{file_id}/metadata` - Get file metadata
- [ ] `POST /api/v1/media/{file_id}/process` - Trigger processing

**Storage Admin**:
- [ ] `GET /api/v1/storage/usage` - Get storage usage stats
- [ ] `GET /api/v1/storage/buckets` - List buckets
- [ ] `POST /api/v1/storage/cleanup` - Trigger cleanup
- [ ] `GET /api/v1/storage/health` - Storage health check

### Phase 2: Multi-Tenancy API Endpoints (Priority: HIGH)

Tenant models exist but missing middleware and API endpoints!

**Files to Create:**
- [ ] `apps/backend/api/v1/endpoints/tenant_admin.py` - Tenant management
- [ ] `apps/backend/api/v1/endpoints/tenant_settings.py` - Tenant config
- [ ] `apps/backend/api/v1/endpoints/tenant_billing.py` - Tenant billing
- [ ] `apps/backend/middleware/tenant_middleware.py` - Tenant isolation

**Tenant Admin Endpoints**:
- [ ] `POST /api/v1/tenants` - Create new tenant
- [ ] `GET /api/v1/tenants` - List all tenants (admin)
- [ ] `GET /api/v1/tenants/{tenant_id}` - Get tenant details
- [ ] `PATCH /api/v1/tenants/{tenant_id}` - Update tenant
- [ ] `DELETE /api/v1/tenants/{tenant_id}` - Delete tenant
- [ ] `POST /api/v1/tenants/{tenant_id}/provision` - Provision tenant
- [ ] `POST /api/v1/tenants/{tenant_id}/migrate` - Migrate tenant data

**Tenant Settings Endpoints**:
- [ ] `GET /api/v1/tenant/settings` - Get current tenant settings
- [ ] `PATCH /api/v1/tenant/settings` - Update tenant settings
- [ ] `GET /api/v1/tenant/features` - Get enabled features
- [ ] `PATCH /api/v1/tenant/features` - Toggle features
- [ ] `GET /api/v1/tenant/limits` - Get usage limits
- [ ] `PATCH /api/v1/tenant/limits` - Update limits (admin)

**Tenant Billing Endpoints**:
- [ ] `GET /api/v1/tenant/billing/usage` - Current usage
- [ ] `GET /api/v1/tenant/billing/invoices` - List invoices
- [ ] `GET /api/v1/tenant/billing/subscription` - Get subscription
- [ ] `POST /api/v1/tenant/billing/subscription` - Update subscription

### Phase 3: Enhanced Content Management API (Priority: MEDIUM)

**Files to Create/Update:**
- [ ] `apps/backend/api/v1/endpoints/content_versions.py` - Version control
- [ ] `apps/backend/api/v1/endpoints/content_workflow.py` - Workflow management
- [ ] `apps/backend/api/v1/endpoints/content_tags.py` - Tag management

**Content Versioning**:
- [ ] `GET /api/v1/content/{content_id}/versions` - List versions
- [ ] `GET /api/v1/content/{content_id}/versions/{version}` - Get version
- [ ] `POST /api/v1/content/{content_id}/revert` - Revert to version
- [ ] `GET /api/v1/content/{content_id}/diff` - Compare versions

**Content Workflow**:
- [ ] `POST /api/v1/content/{content_id}/submit` - Submit for review
- [ ] `POST /api/v1/content/{content_id}/approve` - Approve content
- [ ] `POST /api/v1/content/{content_id}/reject` - Reject content
- [ ] `POST /api/v1/content/{content_id}/publish` - Publish content
- [ ] `GET /api/v1/content/workflow/pending` - Pending reviews

**Tag Management**:
- [ ] `GET /api/v1/tags` - List all tags
- [ ] `POST /api/v1/tags` - Create tag
- [ ] `PATCH /api/v1/tags/{tag_id}` - Update tag
- [ ] `DELETE /api/v1/tags/{tag_id}` - Delete tag
- [ ] `GET /api/v1/tags/popular` - Most used tags

### Phase 4: Analytics & Reporting API (Priority: MEDIUM)

**Files to Create:**
- [ ] `apps/backend/api/v1/endpoints/analytics_reports.py` - Report generation
- [ ] `apps/backend/api/v1/endpoints/analytics_export.py` - Data export
- [ ] `apps/backend/api/v1/endpoints/analytics_dashboards.py` - Dashboard data

**Reporting Endpoints**:
- [ ] `GET /api/v1/analytics/reports` - List available reports
- [ ] `POST /api/v1/analytics/reports/{report_id}/generate` - Generate report
- [ ] `GET /api/v1/analytics/reports/{report_id}/results` - Get results
- [ ] `POST /api/v1/analytics/reports/custom` - Create custom report
- [ ] `GET /api/v1/analytics/reports/{report_id}/schedule` - Get schedule
- [ ] `POST /api/v1/analytics/reports/{report_id}/schedule` - Schedule report

**Export Endpoints**:
- [ ] `POST /api/v1/analytics/export/csv` - Export to CSV
- [ ] `POST /api/v1/analytics/export/excel` - Export to Excel
- [ ] `POST /api/v1/analytics/export/pdf` - Export to PDF
- [ ] `GET /api/v1/analytics/export/{export_id}/status` - Export status
- [ ] `GET /api/v1/analytics/export/{export_id}/download` - Download export

**Dashboard Endpoints**:
- [ ] `GET /api/v1/analytics/dashboards` - List dashboards
- [ ] `GET /api/v1/analytics/dashboards/{dashboard_id}` - Get dashboard
- [ ] `POST /api/v1/analytics/dashboards` - Create dashboard
- [ ] `PATCH /api/v1/analytics/dashboards/{dashboard_id}` - Update dashboard

### Phase 5: User Management API Enhancement (Priority: MEDIUM)

**Files to Create:**
- [ ] `apps/backend/api/v1/endpoints/user_preferences.py` - User preferences
- [ ] `apps/backend/api/v1/endpoints/user_notifications.py` - Notifications
- [ ] `apps/backend/api/v1/endpoints/user_activity.py` - Activity tracking

**Preferences Endpoints**:
- [ ] `GET /api/v1/users/me/preferences` - Get user preferences
- [ ] `PATCH /api/v1/users/me/preferences` - Update preferences
- [ ] `POST /api/v1/users/me/preferences/reset` - Reset to defaults
- [ ] `GET /api/v1/users/me/theme` - Get theme settings
- [ ] `PATCH /api/v1/users/me/theme` - Update theme

**Notifications Endpoints**:
- [ ] `GET /api/v1/users/me/notifications` - List notifications
- [ ] `PATCH /api/v1/users/me/notifications/{id}/read` - Mark as read
- [ ] `POST /api/v1/users/me/notifications/read-all` - Mark all read
- [ ] `DELETE /api/v1/users/me/notifications/{id}` - Delete notification
- [ ] `GET /api/v1/users/me/notifications/settings` - Get notification settings
- [ ] `PATCH /api/v1/users/me/notifications/settings` - Update settings

**Activity Endpoints**:
- [ ] `GET /api/v1/users/me/activity` - Get user activity log
- [ ] `GET /api/v1/users/me/activity/stats` - Activity statistics
- [ ] `GET /api/v1/users/me/sessions` - List active sessions
- [ ] `DELETE /api/v1/users/me/sessions/{id}` - Terminate session

### Phase 6: API Documentation (Priority: HIGH)

**Tasks**:
- [ ] Generate OpenAPI 3.1 spec from FastAPI
- [ ] Add comprehensive request/response examples
- [ ] Create API usage guide with code samples
- [ ] Document authentication flows
- [ ] Add rate limiting documentation
- [ ] Create error code reference
- [ ] Build interactive API explorer (Swagger UI)
- [ ] Generate Postman collection

**Files to Create**:
- [ ] `docs/api/API_GUIDE.md` - Comprehensive API guide
- [ ] `docs/api/AUTHENTICATION.md` - Auth documentation
- [ ] `docs/api/ERROR_CODES.md` - Error reference
- [ ] `docs/api/RATE_LIMITING.md` - Rate limiting guide
- [ ] `docs/api/EXAMPLES.md` - Code examples
- [ ] `docs/api/postman_collection.json` - Postman collection

### Phase 7: API Testing (Priority: CRITICAL)

**Test Files to Create**:
- [ ] `tests/api/test_uploads_api.py` - Upload endpoint tests
- [ ] `tests/api/test_media_api.py` - Media endpoint tests
- [ ] `tests/api/test_tenant_api.py` - Tenant endpoint tests
- [ ] `tests/api/test_content_versioning.py` - Version control tests
- [ ] `tests/api/test_analytics_api.py` - Analytics endpoint tests
- [ ] `tests/api/test_user_preferences.py` - Preferences tests

**Test Coverage Targets**:
- [ ] Upload/Media endpoints: 100% coverage
- [ ] Tenant endpoints: 100% coverage
- [ ] Content management: 90% coverage
- [ ] Analytics endpoints: 90% coverage
- [ ] User management: 95% coverage

**Integration Tests**:
- [ ] Test full upload workflow (multipart)
- [ ] Test tenant provisioning flow
- [ ] Test content approval workflow
- [ ] Test report generation and export
- [ ] Test notification delivery

### Phase 8: API Performance & Optimization (Priority: MEDIUM)

**Tasks**:
- [ ] Add response caching for frequent queries
- [ ] Implement pagination for all list endpoints
- [ ] Add field filtering (sparse fieldsets)
- [ ] Implement batch operations
- [ ] Add compression middleware
- [ ] Optimize database queries (N+1 prevention)
- [ ] Add query result caching with Redis
- [ ] Implement API response time monitoring

**Performance Targets**:
- Upload endpoint: < 500ms (excluding file transfer)
- List endpoints: < 200ms
- Analytics queries: < 1s
- Report generation: < 5s

### Phase 9: API Security Enhancement (Priority: HIGH)

**Tasks**:
- [ ] Add request validation middleware
- [ ] Implement rate limiting per endpoint
- [ ] Add API key authentication option
- [ ] Implement request signing for sensitive ops
- [ ] Add CORS configuration per endpoint
- [ ] Implement SQL injection prevention
- [ ] Add request size limits
- [ ] Implement IP-based rate limiting

**Security Files to Create**:
- [ ] `apps/backend/middleware/api_validation.py` - Request validation
- [ ] `apps/backend/middleware/api_rate_limit.py` - Endpoint rate limiting
- [ ] `apps/backend/core/security/request_signing.py` - Request signing

### Phase 10: API Versioning Strategy (Priority: MEDIUM)

**Tasks**:
- [ ] Implement API version routing (/v1, /v2)
- [ ] Create version deprecation strategy
- [ ] Add version headers support
- [ ] Create v2 API structure (future)
- [ ] Document version migration guide
- [ ] Add version compatibility tests

## File Locations

### API Endpoints
- **Storage**: `apps/backend/api/v1/endpoints/uploads.py`, `media.py`
- **Tenants**: `apps/backend/api/v1/endpoints/tenant_*.py`
- **Content**: `apps/backend/api/v1/endpoints/content_*.py`
- **Analytics**: `apps/backend/api/v1/endpoints/analytics_*.py`
- **Users**: `apps/backend/api/v1/endpoints/user_*.py`

### Middleware
- **Tenant**: `apps/backend/middleware/tenant_middleware.py`
- **Validation**: `apps/backend/middleware/api_validation.py`
- **Rate Limiting**: `apps/backend/middleware/api_rate_limit.py`

### Documentation
- **API Guide**: `docs/api/API_GUIDE.md`
- **OpenAPI Spec**: `docs/api/openapi-spec.yaml`
- **Postman**: `docs/api/postman_collection.json`

### Tests
- **API Tests**: `tests/api/test_*.py`
- **Integration Tests**: `tests/integration/api/`

## Technology Stack (2025)

### Backend API
```python
dependencies = {
    "fastapi": "^0.115.0",
    "pydantic": "^2.10.0",
    "sqlalchemy": "^2.0.35",
    "asyncpg": "^0.30.0",
    "redis": "^5.2.0",
    "python-multipart": "^0.0.16",  # File uploads
    "aiofiles": "^24.1.0",  # Async file operations
}
```

### Documentation
```json
{
  "openapi": "3.1.0",
  "swagger-ui": "Latest",
  "redoc": "Latest"
}
```

## Modern API Patterns (2025)

### FastAPI Endpoint Example
```python
# ✅ CORRECT - FastAPI async endpoint with Pydantic v2
from fastapi import APIRouter, UploadFile, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])

class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: str
    filename: str
    size: int
    url: str
    created_at: datetime

@router.post("/file", response_model=UploadResponse)
async def upload_file(
    file: UploadFile,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> UploadResponse:
    """Upload a single file to storage."""
    # Validate file
    if file.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=413, detail="File too large")

    # Use storage service
    storage_service = StorageService(session)
    result = await storage_service.upload_file(
        file=file,
        user_id=current_user.id
    )

    return UploadResponse(**result)
```

### Tenant Middleware Example
```python
# ✅ CORRECT - Tenant isolation middleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from header or subdomain
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id and "tenant" in request.path_params:
            tenant_id = request.path_params["tenant"]

        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant ID required")

        # Validate tenant exists
        tenant = await get_tenant(tenant_id)
        if not tenant or not tenant.is_active:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Add to request state
        request.state.tenant = tenant
        request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response
```

## Commands

### Development
```bash
# Start API server
cd apps/backend
uvicorn main:app --host 0.0.0.0 --port 8019 --reload

# Generate OpenAPI spec
python scripts/generate_openapi.py > docs/api/openapi-spec.yaml

# Test specific endpoint
pytest tests/api/test_uploads_api.py -v

# Test all API endpoints
pytest tests/api/ -v

# Check API documentation
open http://localhost:8019/docs  # Swagger UI
open http://localhost:8019/redoc  # ReDoc
```

### Testing
```bash
# Run API tests with coverage
pytest tests/api/ --cov=apps/backend/api --cov-report=html

# Test specific endpoint
pytest tests/api/test_uploads_api.py::test_upload_file -v

# Integration tests
pytest tests/integration/api/ -v

# Load testing
locust -f tests/load/test_api.py --host http://localhost:8019
```

## Performance Targets

- **Upload Endpoint**: < 500ms response (excluding file transfer)
- **List Endpoints**: < 200ms p95
- **Search Endpoints**: < 500ms p95
- **Analytics Queries**: < 1s p95
- **Report Generation**: < 5s for standard reports
- **Throughput**: > 1000 req/s per endpoint

## Success Metrics

- ✅ All storage endpoints implemented (8+)
- ✅ All tenant endpoints implemented (15+)
- ✅ All content management endpoints enhanced
- ✅ All analytics endpoints created
- ✅ All user management endpoints enhanced
- ✅ 100% OpenAPI documentation coverage
- ✅ 90%+ test coverage for all endpoints
- ✅ All endpoints under performance targets
- ✅ Zero security vulnerabilities
- ✅ API versioning strategy implemented

---

**REMEMBER**: APIs are the contract with the frontend. Design them well, document them thoroughly, and test them comprehensively!
