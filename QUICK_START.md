# Backend Development - Quick Start Guide

**Worktree**: backend-dev | **Branch**: development | **Port**: 8011

---

## 🚀 Start Backend Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start backend on port 8011
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8011 --reload

# Or use Makefile
make backend
```

---

## 📊 New Metrics Endpoints

### 1. Dashboard Metrics
```bash
curl -X GET "http://localhost:8011/api/v1/metrics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Force refresh cache
curl -X GET "http://localhost:8011/api/v1/metrics/dashboard?force_refresh=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Activity Metrics (Recent 24h)
```bash
curl -X GET "http://localhost:8011/api/v1/metrics/activity" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Statistics
```bash
# Available periods: 24h, 7d, 30d, 90d
curl -X GET "http://localhost:8011/api/v1/metrics/statistics?period=7d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Export Metrics
```bash
curl -X POST "http://localhost:8011/api/v1/metrics/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "date_range": "7d",
    "metric_types": ["users", "content", "engagement"]
  }'
```

### 5. Invalidate Cache (Admin Only)
```bash
curl -X POST "http://localhost:8011/api/v1/metrics/invalidate-cache" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 🧪 Run Tests

```bash
# All integration tests
pytest tests/integration/test_metrics_api.py -v

# Specific test class
pytest tests/integration/test_metrics_api.py::TestDashboardMetricsAPI -v

# With coverage report
pytest tests/integration/test_metrics_api.py --cov=apps.backend.api.v1.endpoints.metrics --cov-report=html
```

---

## 📖 API Documentation

- **Swagger UI**: http://localhost:8011/docs
- **ReDoc**: http://localhost:8011/redoc
- **OpenAPI JSON**: http://localhost:8011/openapi.json

---

## 🔍 Monitor Requests

All requests now include correlation IDs:

```bash
# Check response headers
curl -I -X GET "http://localhost:8011/api/v1/metrics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Headers you'll see:
# X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
# X-Request-ID: 7c9e6679-7425-40de-944b-e07fc1f90ae7
# X-Request-Duration: 0.145s
# X-RateLimit-Limit: 10
# X-RateLimit-Remaining: 9
# X-RateLimit-Reset: 1633024800
```

---

## 📊 Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/v1/metrics/dashboard` | 10 req/min |
| `/api/v1/metrics/activity` | 20 req/min |
| `/api/v1/metrics/statistics` | 30 req/min |
| `/api/v1/metrics/export` | 10 req/hour |

**User Tier Multipliers:**
- Free: 1x (base limits)
- Basic: 2x
- Premium: 5x
- Enterprise: 10x

---

## 🗄️ Database Indexes

Recommended indexes for performance (run in PostgreSQL):

```sql
-- User queries
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_last_login ON users(last_login DESC);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Content queries
CREATE INDEX idx_content_organization_id ON educational_content(organization_id);
CREATE INDEX idx_content_status ON educational_content(status);
CREATE INDEX idx_content_created_at ON educational_content(created_at DESC);

-- Lessons/Assessments
CREATE INDEX idx_lessons_created_at ON lessons(created_at DESC);
CREATE INDEX idx_assessments_created_at ON assessments(created_at DESC);
```

---

## 🐛 Debugging

### Check Logs with Correlation IDs
```bash
# Tail logs
tail -f logs/backend.log | grep "correlation_id"

# Search for specific request
grep "550e8400-e29b-41d4-a716-446655440000" logs/backend.log
```

### Monitor Redis Cache
```bash
# Connect to Redis
redis-cli

# Check cache keys
KEYS dashboard:metrics:*

# View cached data
GET dashboard:metrics:org-123

# Monitor cache hits/misses
MONITOR
```

### Check Rate Limits
```bash
# Check Redis rate limit keys
redis-cli KEYS rate_limit:*

# View specific user's rate limit
redis-cli GET "rate_limit:metrics:dashboard:user:user-123"
```

---

## 🔄 Development Workflow

### 1. Make Changes
```bash
# Edit files in apps/backend/
code apps/backend/api/v1/endpoints/metrics.py
```

### 2. Test Changes
```bash
# Run tests
pytest tests/integration/test_metrics_api.py -v

# Check type hints
mypy apps/backend/api/v1/endpoints/metrics.py
```

### 3. Restart Server
```bash
# Server auto-reloads with --reload flag
# Or manually restart:
pkill -f "uvicorn main:app"
uvicorn main:app --host 127.0.0.1 --port 8011 --reload
```

### 4. Verify in Browser
```bash
# Open Swagger docs
open http://localhost:8011/docs

# Test endpoint
curl -X GET "http://localhost:8011/api/v1/metrics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📁 File Locations

### New Files Created
```
apps/backend/
├── api/v1/endpoints/
│   └── metrics.py                    # Metrics API endpoints
├── services/
│   └── dashboard_metrics_service.py  # Metrics service
└── middleware/
    └── correlation_id.py             # Correlation ID middleware

tests/integration/
└── test_metrics_api.py               # Integration tests
```

### Existing Files Used
```
apps/backend/
├── core/
│   ├── rate_limiter.py               # Rate limiting (existing)
│   ├── cache.py                      # Redis caching (existing)
│   └── config.py                     # Configuration (existing)
└── middleware/
    ├── prometheus_middleware.py      # Prometheus metrics (existing)
    └── tenant.py                     # Multi-tenancy (existing)
```

---

## 🎯 Common Tasks

### Add New Metric
```python
# 1. Add field to Pydantic model
class UserMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    new_metric: int = Field(default=0, description="New metric")

# 2. Add calculation in service
async def _get_user_metrics(self, session, org_id):
    new_metric_query = select(func.count(Model.id)).where(...)
    result = await session.execute(new_metric_query)
    new_metric = result.scalar() or 0

    return UserMetrics(new_metric=new_metric, ...)
```

### Change Cache TTL
```python
# In dashboard_metrics_service.py
self._cache_ttl_metrics = CacheConfig.LONG_TTL  # 1 hour
self._cache_ttl_activity = CacheConfig.MEDIUM_TTL  # 15 minutes
```

### Modify Rate Limits
```python
# In metrics.py
config = RateLimitConfig(
    requests_per_minute=50,  # Increase from 30
    endpoint_limits={
        "/api/v1/metrics/dashboard": {"requests_per_minute": 20},  # Increase from 10
    }
)
```

---

## 🚨 Troubleshooting

### Issue: Redis Connection Error
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Start Redis if needed
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### Issue: Rate Limit Always Triggered
```bash
# Clear rate limit keys in Redis
redis-cli
> FLUSHDB  # Warning: Clears all data in current DB

# Or selectively delete
> DEL rate_limit:*
```

### Issue: Cache Not Working
```bash
# Check Redis connection in logs
grep "Redis" logs/backend.log

# Manually test cache
redis-cli
> SET test "value"
> GET test
```

### Issue: Tests Failing
```bash
# Clear pytest cache
rm -rf .pytest_cache

# Run with verbose output
pytest tests/integration/test_metrics_api.py -vv

# Run single test
pytest tests/integration/test_metrics_api.py::TestDashboardMetricsAPI::test_get_dashboard_metrics_success -vv
```

---

## 📚 Additional Resources

- **Full Implementation**: See `BACKEND_DEV_IMPLEMENTATION.md`
- **Backend Analysis**: See `BACKEND_ANALYSIS.md`
- **API Docs**: http://localhost:8011/docs
- **2025 Standards**: All code follows official 2025 Python/FastAPI patterns

---

**Last Updated**: 2025-10-01
**Maintainer**: Backend Development Team
**Status**: ✅ Production Ready
