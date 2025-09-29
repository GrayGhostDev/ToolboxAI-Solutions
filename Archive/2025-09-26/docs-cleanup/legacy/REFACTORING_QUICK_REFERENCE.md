# ToolboxAI Backend - Quick Reference Guide
*Post-Refactoring Architecture (September 2025)*

## 🚀 Quick Start

### Starting the Refactored Backend
```bash
# Navigate to project root
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Activate virtual environment
source venv/bin/activate

# Start backend (now using factory pattern)
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload

# Alternative: Use make command
make backend
```

### Health Check
```bash
# Check system status
curl http://localhost:8009/health

# Check refactoring status
curl http://localhost:8009/migration/status

# Expected response includes:
# {"status": "completed", "line_reduction": "from_4400+_to_<100_lines"}
```

## 📁 New Architecture Layout

### Core Modules (apps/backend/core/)
```
core/
├── app_factory.py      # 🏭 Application factory pattern
├── config.py           # ⚙️ Centralized configuration
├── logging.py          # 📝 Structured logging with correlation IDs
├── middleware.py       # 🔧 Middleware registry and management
├── lifecycle.py        # 🔄 Startup/shutdown lifecycle
├── monitoring.py       # 📊 Sentry and performance monitoring
├── security/           # 🔒 Security modules
│   ├── cors.py        # CORS configuration
│   ├── jwt_handler.py # JWT token management
│   ├── middleware.py  # Security middleware
│   └── headers.py     # Security headers
└── errors/            # ⚠️ Error handling
    ├── middleware.py  # Error middleware
    └── handlers.py    # Custom error handlers
```

### What Changed
- **main.py**: 4,430 lines → 60 lines (91.8% reduction)
- **Structure**: Monolith → Modular factory pattern
- **Dependencies**: Centralized → Injected
- **Configuration**: Scattered → `core/config.py`
- **Logging**: Basic → Structured with correlation IDs
- **Middleware**: Inline → Registry pattern

## 🛠️ Developer Workflows

### Adding New Endpoints
```python
# 1. Create endpoint module (preferred approach)
# apps/backend/api/v1/endpoints/my_feature.py

from fastapi import APIRouter, Depends
from apps.backend.core.logging import logging_manager
from apps.backend.models.schemas import BaseResponse

router = APIRouter(prefix="/my-feature", tags=["my-feature"])
logger = logging_manager.get_logger(__name__)

@router.get("/", response_model=BaseResponse)
async def get_my_feature():
    logger.info("My feature endpoint accessed")
    return BaseResponse(
        status="success",
        data={"message": "Hello from my feature"},
        message="Feature accessed successfully"
    )

# 2. Register router (when router registry is complete)
# Will be in apps/backend/api/routers/__init__.py
```

### Adding New Services
```python
# 1. Create service module
# apps/backend/services/my_service.py

from apps.backend.core.logging import logging_manager
from apps.backend.core.config import settings

logger = logging_manager.get_logger(__name__)

class MyService:
    def __init__(self):
        self.config = settings
        logger.info("MyService initialized")

    async def do_something(self, data: str) -> str:
        logger.info(f"Processing data: {data}")
        # Your business logic here
        return f"Processed: {data}"

# 2. Create dependency provider
# apps/backend/core/deps.py

_my_service_instance = None

async def get_my_service() -> MyService:
    global _my_service_instance
    if _my_service_instance is None:
        _my_service_instance = MyService()
    return _my_service_instance

# 3. Use in endpoints
from fastapi import Depends
from apps.backend.core.deps import get_my_service

@router.post("/process")
async def process_data(
    data: str,
    my_service: MyService = Depends(get_my_service)
):
    result = await my_service.do_something(data)
    return {"result": result}
```

### Adding New Middleware
```python
# 1. Create middleware
# apps/backend/core/middleware/my_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from apps.backend.core.logging import logging_manager

logger = logging_manager.get_logger(__name__)

class MyCustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        logger.info(f"Custom middleware processing: {request.url}")

        # Pre-processing
        start_time = time.time()

        # Call next middleware/endpoint
        response = await call_next(request)

        # Post-processing
        process_time = time.time() - start_time
        logger.info(f"Request processed in {process_time:.4f}s")

        return response

# 2. Register in middleware.py
# apps/backend/core/middleware.py

def register_middleware(app: FastAPI):
    # ... existing middleware ...
    app.add_middleware(MyCustomMiddleware)
```

### Configuration Management
```python
# All configuration in apps/backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Add new config variables here
    MY_NEW_SETTING: str = "default_value"
    MY_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"

# Usage anywhere in the app
from apps.backend.core.config import settings

def my_function():
    api_key = settings.MY_API_KEY
    if not api_key:
        raise ValueError("MY_API_KEY not configured")
```

### Logging Best Practices
```python
from apps.backend.core.logging import logging_manager

logger = logging_manager.get_logger(__name__)

# Structured logging with extra fields
logger.info(
    "User action performed",
    extra_fields={
        "user_id": user.id,
        "action": "create_content",
        "content_type": "lesson"
    }
)

# Error logging with context
try:
    result = await some_operation()
except Exception as e:
    logger.error(
        f"Operation failed: {e}",
        extra_fields={
            "operation": "some_operation",
            "user_id": user.id,
            "error_type": type(e).__name__
        }
    )
    raise
```

## 🧪 Testing

### Testing the Refactored Backend
```python
# Create test apps using factory
from apps.backend.core.app_factory import create_test_app

def test_my_endpoint():
    app = create_test_app()  # Gets clean app without external deps
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

# Test individual components
def test_my_service():
    from apps.backend.services.my_service import MyService
    service = MyService()
    result = await service.do_something("test")
    assert result == "Processed: test"
```

### Running Tests
```bash
# All tests
pytest -v

# Backend-specific tests
pytest apps/backend/tests/ -v

# Test with coverage
pytest --cov=apps/backend --cov-report=html

# Specific test file
pytest tests/unit/core/test_app_factory.py -v
```

## 🐛 Debugging

### Checking Application State
```python
# Check if factory components are loaded
curl http://localhost:8009/migration/status

# Look for these in the response:
# "status": "completed"
# "architecture_improvements": {...}
# "line_reduction": "from_4400+_to_<100_lines"
```

### Common Issues

#### Import Errors
```bash
# If you see import errors, check:
1. Virtual environment is activated: `source venv/bin/activate`
2. Dependencies installed: `pip install -r requirements.txt`
3. Python path is correct
```

#### Factory Component Issues
```python
# Check apps/backend/core/app_factory.py logs for:
# "Factory components not yet available"
# This indicates missing dependencies in core modules
```

#### Middleware Registration Issues
```python
# In apps/backend/core/middleware.py, look for:
# "Resilience middleware not available"
# This is expected - some middleware is optional
```

## 📚 Key Files Reference

### Essential Files to Know
```
apps/backend/
├── main.py                    # 60 lines - Entry point using factory
├── main_original.py           # 4,430 lines - Original backup
├── core/
│   ├── app_factory.py        # App creation logic
│   ├── config.py             # All configuration
│   ├── logging.py            # Logging setup
│   └── middleware.py         # Middleware registry
├── api/v1/endpoints/         # API endpoints
├── services/                 # Business logic
└── models/                   # Data models
```

### Migration Artifacts
- **main_original.py**: Complete backup of original file
- **migration/status endpoint**: Live migration status
- **REFACTORING_COMPLETE.md**: Full documentation
- **Factory pattern**: All new components follow this pattern

## 🔄 Rollback Procedure (Emergency)

If critical issues arise:
```bash
# 1. Stop the server
pkill -f uvicorn

# 2. Restore original (emergency only)
cp apps/backend/main_original.py apps/backend/main.py

# 3. Restart
uvicorn apps.backend.main:app --port 8009

# Note: This loses all refactoring benefits
# Better to fix specific issues in the modular code
```

## 🎯 Best Practices

### Do's
- ✅ Use the factory pattern for new components
- ✅ Follow the modular structure
- ✅ Add proper logging with correlation IDs
- ✅ Use dependency injection patterns
- ✅ Follow the separation of concerns
- ✅ Add comprehensive error handling

### Don'ts
- ❌ Don't add code directly to main.py
- ❌ Don't skip the factory pattern
- ❌ Don't mix concerns in modules
- ❌ Don't ignore the middleware registry
- ❌ Don't bypass the configuration system

## 📞 Support

### Troubleshooting Steps
1. Check `/migration/status` endpoint
2. Review logs in console output
3. Verify virtual environment activation
4. Check configuration in `core/config.py`
5. Ensure all dependencies are installed

### Documentation
- **Full Architecture**: `REFACTORING_COMPLETE.md`
- **API Docs**: http://localhost:8009/docs
- **Config Reference**: `apps/backend/core/config.py`
- **Project Guide**: `CLAUDE.md`

---

*Refactored Backend Quick Reference - September 2025*
*ToolboxAI Engineering Team*