# ToolBoxAI Post-Deployment Implementation Plan

**Created:** November 13, 2025
**Status:** Active
**Backend Deployment:** ✅ Successful (Render)
**Frontend Deployment:** ⏳ Pending (Vercel)
**Priority:** HIGH

---

## 🎯 Executive Summary

The ToolBoxAI backend has been successfully deployed to Render with 178 API endpoints operational. This document outlines the structured plan to complete the remaining configuration, testing, optimization, and frontend deployment tasks.

**Current State:**
- ✅ Backend deployed and serving requests
- ✅ 178 API endpoints registered
- ✅ OpenAPI documentation accessible
- ⚠️ Database connection requires configuration
- ⚠️ Pusher real-time service requires configuration
- ⚠️ Minor TypeError in router registration (non-critical)

**Goal State:**
- ✅ All services fully configured and connected
- ✅ Frontend deployed to Vercel
- ✅ Full-stack integration tested and verified
- ✅ Monitoring and alerting operational
- ✅ All code quality issues resolved

---

## 📋 Implementation Phases

### **Phase 1: Environment Configuration** 🔧
**Priority:** CRITICAL
**Estimated Time:** 1-2 hours
**Dependencies:** None

#### Objectives
1. Configure all missing Render environment variables
2. Establish database connection
3. Enable Pusher real-time communication
4. Verify all service integrations

#### Step-by-Step Actions

##### 1.1 Environment Variable Audit
```bash
# Step 1: Review current Render environment variables
# Access: Render Dashboard → toolboxai-backend-8j12 → Environment

# Step 2: Compare with .env.example template
cat .env.example | grep -E "^[A-Z_]+=" | cut -d'=' -f1 | sort > required_vars.txt

# Step 3: Identify missing variables
# Required variables checklist:
```

**Required Environment Variables:**

**Database:**
- `DATABASE_URL` - PostgreSQL connection string (Supabase)
- `DATABASE_POOL_SIZE` - Default: 20
- `DATABASE_MAX_OVERFLOW` - Default: 10

**Redis:**
- `REDIS_URL` - Redis connection string (already configured ✅)

**Pusher:**
- `PUSHER_APP_ID` - Pusher application ID
- `PUSHER_KEY` - Pusher public key
- `PUSHER_SECRET` - Pusher secret key
- `PUSHER_CLUSTER` - Pusher cluster (e.g., 'us2')

**OpenAI:**
- `OPENAI_API_KEY` - OpenAI API key (already configured ✅)
- `OPENAI_ORG_ID` - OpenAI organization ID

**Authentication (Clerk):**
- `CLERK_SECRET_KEY` - Clerk backend secret
- `CLERK_PUBLISHABLE_KEY` - Clerk frontend key
- `CLERK_WEBHOOK_SECRET` - Webhook verification secret

**Email (SendGrid):**
- `SENDGRID_API_KEY` - SendGrid API key
- `SENDGRID_FROM_EMAIL` - Sender email address
- `SENDGRID_FROM_NAME` - Sender name

**Stripe (Payments):**
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe public key
- `STRIPE_WEBHOOK_SECRET` - Webhook signing secret

**Supabase:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon/service key

**Application:**
- `ENVIRONMENT` - "production"
- `DEBUG` - "false"
- `LOG_LEVEL` - "INFO"
- `ALLOWED_ORIGINS` - Frontend URL (Vercel)

##### 1.2 Configure Database Connection

```bash
# Option A: Supabase Postgres (Recommended)
# 1. Get connection string from Supabase dashboard
# 2. Format: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
# 3. Add to Render environment variables

# Option B: Render PostgreSQL
# 1. Create PostgreSQL instance in Render
# 2. Copy internal connection URL
# 3. Add DATABASE_URL to environment variables

# Test connection after configuration:
curl -s "https://toolboxai-backend-8j12.onrender.com/health" | jq '.checks.database'
# Expected: true
```

**Configuration Steps:**
1. Access Render Dashboard → Environment Tab
2. Add `DATABASE_URL` with Supabase connection string
3. Set `DATABASE_POOL_SIZE=20`
4. Set `DATABASE_MAX_OVERFLOW=10`
5. Save and redeploy service
6. Wait for deployment completion (~2 minutes)
7. Verify health check shows `database: true`

##### 1.3 Configure Pusher Real-Time

```bash
# 1. Get Pusher credentials from dashboard.pusher.com
# 2. Add to Render environment variables:

PUSHER_APP_ID=1234567
PUSHER_KEY=abcdef123456
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2

# 3. Test connection after configuration:
curl -s "https://toolboxai-backend-8j12.onrender.com/health" | jq '.checks.pusher'
# Expected: true
```

**Configuration Steps:**
1. Log in to Pusher dashboard
2. Select ToolBoxAI application (or create new)
3. Copy App ID, Key, Secret, and Cluster
4. Add all four variables to Render environment
5. Save and redeploy
6. Verify health check shows `pusher: true`

##### 1.4 Verify Service Integrations

**Verification Script:**
```bash
#!/bin/bash
# File: scripts/deployment/verify-services.sh

BACKEND_URL="https://toolboxai-backend-8j12.onrender.com"

echo "🔍 Verifying Service Integrations..."

# Test health endpoint
HEALTH=$(curl -s "$BACKEND_URL/health")

# Check each service
echo "Database: $(echo $HEALTH | jq -r '.checks.database')"
echo "Redis: $(echo $HEALTH | jq -r '.checks.redis')"
echo "Pusher: $(echo $HEALTH | jq -r '.checks.pusher')"
echo "Supabase: $(echo $HEALTH | jq -r '.checks.supabase')"
echo "Agents: $(echo $HEALTH | jq -r '.checks.agents')"

# Overall status
echo "Status: $(echo $HEALTH | jq -r '.status')"
# Expected: "healthy" (not "degraded")
```

#### Acceptance Criteria
- [ ] All required environment variables configured in Render
- [ ] DATABASE_URL set and database connection successful (`database: true`)
- [ ] PUSHER_* credentials set and connection successful (`pusher: true`)
- [ ] Health endpoint returns `"status": "healthy"`
- [ ] No connection errors in Render logs

#### Risk Assessment
- **Low Risk:** Environment variable configuration is straightforward
- **Mitigation:** Keep backup of current working configuration
- **Rollback:** Revert to previous environment variables if issues occur

---

### **Phase 2: Testing and Verification** 🧪
**Priority:** HIGH
**Estimated Time:** 2-3 hours
**Dependencies:** Phase 1 complete

#### Objectives
1. Verify agent system lazy initialization
2. Test critical API endpoints
3. Validate authentication flows
4. Confirm real-time features work

#### Step-by-Step Actions

##### 2.1 Test Agent System Initialization

**Test Script:**
```bash
#!/bin/bash
# File: scripts/deployment/test-agent-system.sh

BACKEND_URL="https://toolboxai-backend-8j12.onrender.com"

echo "🤖 Testing Agent System..."

# 1. Check initial agent health (should trigger lazy init)
echo "Testing /api/v1/agents/health..."
AGENT_HEALTH=$(curl -s "$BACKEND_URL/api/v1/agents/health")
echo "Response: $AGENT_HEALTH"

# 2. Test content generation endpoint (uses agents)
echo ""
echo "Testing content generation..."
curl -X POST "$BACKEND_URL/api/v1/enhanced-content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "quiz",
    "subject": "mathematics",
    "grade_level": "5th_grade",
    "topic": "fractions"
  }'

# 3. Verify agent pool created
echo ""
echo "Checking health again (agents should be initialized)..."
curl -s "$BACKEND_URL/health" | jq '.checks.agents'
# Expected: true
```

**Manual Testing:**
1. Open Render logs (real-time view)
2. Run test script
3. Watch for log messages:
   - `"Creating AgentManager instance (first access)"`
   - `"AgentPool created (lazy initialization enabled)"`
   - `"Agent pool initialized successfully"`
4. Verify no errors related to ChatOpenAI or httpx.Client

##### 2.2 Test Critical API Endpoints

**Endpoint Test Matrix:**

| Category | Endpoint | Method | Auth Required | Expected Response |
|----------|----------|--------|---------------|-------------------|
| **Authentication** | `/api/v1/auth/verify` | POST | No | 200 with token validation |
| **Users** | `/api/v1/users/me` | GET | Yes | 200 with user data |
| **Content** | `/api/v1/educational-content` | GET | Yes | 200 with content list |
| **Roblox** | `/api/v1/roblox/status` | GET | Yes | 200 with integration status |
| **Analytics** | `/api/v1/analytics/dashboard` | GET | Yes | 200 with analytics data |
| **Tasks** | `/api/v1/tasks/status/{task_id}` | GET | Yes | 200 with task status |

**Automated Test Script:**
```bash
#!/bin/bash
# File: scripts/deployment/test-api-endpoints.sh

BACKEND_URL="https://toolboxai-backend-8j12.onrender.com"
AUTH_TOKEN="your-clerk-jwt-token"  # Get from Clerk dashboard test user

test_endpoint() {
    local endpoint=$1
    local method=$2
    local auth=$3

    echo "Testing ${method} ${endpoint}..."

    if [ "$auth" = "true" ]; then
        response=$(curl -s -w "%{http_code}" \
          -X $method \
          -H "Authorization: Bearer $AUTH_TOKEN" \
          "$BACKEND_URL$endpoint")
    else
        response=$(curl -s -w "%{http_code}" \
          -X $method \
          "$BACKEND_URL$endpoint")
    fi

    http_code="${response: -3}"

    if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
        echo "  ✅ PASS (HTTP $http_code)"
    else
        echo "  ❌ FAIL (HTTP $http_code)"
    fi
}

# Run tests
test_endpoint "/health" "GET" "false"
test_endpoint "/docs" "GET" "false"
test_endpoint "/api/v1" "GET" "false"
test_endpoint "/api/v1/users/me" "GET" "true"
test_endpoint "/api/v1/educational-content" "GET" "true"
test_endpoint "/api/v1/roblox/status" "GET" "true"
```

##### 2.3 Test Authentication Flow

**Clerk Integration Test:**
```bash
# 1. Get test JWT token from Clerk Dashboard
# Navigate to: dashboard.clerk.com → Users → Select test user → Generate JWT

# 2. Test protected endpoint
curl -X GET \
  -H "Authorization: Bearer eyJhbGc..." \
  "https://toolboxai-backend-8j12.onrender.com/api/v1/users/me"

# Expected: 200 with user profile data
# Error cases:
# - 401: Invalid or expired token
# - 403: Insufficient permissions
```

##### 2.4 Test Real-Time Features (Pusher)

**Pusher Connection Test:**
```javascript
// File: scripts/deployment/test-pusher.js
// Run with: node scripts/deployment/test-pusher.js

const Pusher = require('pusher-js');

const pusher = new Pusher('YOUR_PUSHER_KEY', {
  cluster: 'us2',
  encrypted: true
});

const channel = pusher.subscribe('test-channel');

channel.bind('test-event', function(data) {
  console.log('✅ Pusher event received:', data);
  process.exit(0);
});

// Trigger test event from backend
fetch('https://toolboxai-backend-8j12.onrender.com/api/v1/pusher/trigger', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    channel: 'test-channel',
    event: 'test-event',
    data: { message: 'Test from deployment verification' }
  })
});

setTimeout(() => {
  console.log('❌ Timeout - no Pusher event received');
  process.exit(1);
}, 5000);
```

#### Acceptance Criteria
- [ ] Agent system initializes successfully on first API call
- [ ] Health endpoint shows `agents: true` after initialization
- [ ] All critical endpoints return 2xx status codes
- [ ] Authentication flow works with Clerk JWT tokens
- [ ] Pusher events are sent and received successfully
- [ ] No errors in Render logs during testing

---

### **Phase 3: Code Quality Improvements** 🔨
**Priority:** MEDIUM
**Estimated Time:** 3-4 hours
**Dependencies:** Phase 2 complete

#### Objectives
1. Investigate and fix TypeError in router registration
2. Audit all type annotations for Python 3.12 compatibility
3. Ensure BasedPyright type checking passes
4. Remove any remaining circular import warnings

#### Step-by-Step Actions

##### 3.1 Investigate TypeError Root Cause

**Current Error:**
```
TypeError: unsupported operand type(s) for |: 'builtin_function_or_method' and 'NoneType'
Location: apps.backend.api.routers.__init__.py:41
Context: Router registration during application startup
```

**Investigation Steps:**

```python
# File: scripts/analysis/find_type_annotation_issues.py

import ast
import os
from pathlib import Path

def find_problematic_annotations(directory):
    """Find type annotations that might cause runtime errors."""
    issues = []

    for py_file in Path(directory).rglob('*.py'):
        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
            continue

        try:
            with open(py_file, 'r') as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                # Look for BinOp with BitOr operator in annotations
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                    # Check if used in type annotation context
                    if hasattr(node.left, 'id') and node.left.id == 'type':
                        issues.append({
                            'file': str(py_file),
                            'line': node.lineno,
                            'issue': 'Union with builtin type() function',
                            'suggestion': 'Replace with Type[...] from typing'
                        })

        except Exception as e:
            print(f"Error parsing {py_file}: {e}")

    return issues

# Run analysis
issues = find_problematic_annotations('apps/backend/api')
for issue in issues:
    print(f"{issue['file']}:{issue['line']} - {issue['issue']}")
    print(f"  Suggestion: {issue['suggestion']}\n")
```

**Common Causes:**

1. **Using `type` builtin in union:**
   ```python
   # ❌ BAD - type is a builtin function
   def func(param: type | None) -> type:
       pass

   # ✅ GOOD - Use Type from typing
   from typing import Type
   def func(param: Type[Any] | None) -> Type[Any]:
       pass
   ```

2. **Runtime evaluation of string annotations:**
   ```python
   # ❌ BAD - Forward reference evaluated at runtime
   def func() -> "type | None":
       pass

   # ✅ GOOD - Use proper Type annotation
   from __future__ import annotations
   from typing import Type
   def func() -> Type[Any] | None:
       pass
   ```

3. **Pydantic model with improper type:**
   ```python
   # ❌ BAD
   class Model(BaseModel):
       field: type | None = None

   # ✅ GOOD
   from typing import Type
   class Model(BaseModel):
       field: Type[Any] | None = None
   ```

##### 3.2 Fix Identified Type Annotation Issues

**Fix Strategy:**

```bash
# 1. Find all occurrences of problematic pattern
grep -r ": type |" apps/backend/api --include="*.py" -n

# 2. Find all occurrences of reverse pattern
grep -r "| type" apps/backend/api --include="*.py" -n

# 3. Check for Type imports
grep -r "from typing import Type" apps/backend/api --include="*.py" | wc -l
```

**Automated Fix Script:**
```python
# File: scripts/fixes/fix_type_annotations.py

import re
from pathlib import Path

def fix_type_annotations(file_path):
    """Fix type annotation issues in a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content
    changes_made = []

    # Pattern 1: : type | None
    pattern1 = r': type \| None'
    if re.search(pattern1, content):
        # Add Type import if not present
        if 'from typing import' not in content or 'Type' not in content:
            content = re.sub(
                r'(from typing import.*)',
                r'\1, Type',
                content,
                count=1
            )
        content = re.sub(pattern1, ': Type[Any] | None', content)
        changes_made.append('Fixed: type | None → Type[Any] | None')

    # Pattern 2: | type
    pattern2 = r'\| type([^A-Za-z])'
    if re.search(pattern2, content):
        content = re.sub(pattern2, r'| Type[Any]\1', content)
        changes_made.append('Fixed: | type → | Type[Any]')

    # Pattern 3: -> type
    pattern3 = r'-> type:'
    if re.search(pattern3, content):
        content = re.sub(pattern3, '-> Type[Any]:', content)
        changes_made.append('Fixed: -> type → -> Type[Any]')

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed {file_path}")
        for change in changes_made:
            print(f"   {change}")
        return True
    return False

# Run on all API files
api_dir = Path('apps/backend/api')
fixed_count = 0

for py_file in api_dir.rglob('*.py'):
    if fix_type_annotations(py_file):
        fixed_count += 1

print(f"\n🎉 Fixed {fixed_count} files")
```

##### 3.3 Run Type Checking with BasedPyright

```bash
# 1. Ensure BasedPyright is installed
pip install basedpyright

# 2. Run type checking on API module
basedpyright apps/backend/api

# 3. Review and fix any type errors
# Common issues:
# - Missing imports (Type, Any, Optional)
# - Incorrect union syntax
# - Forward reference issues

# 4. Run type checking on entire backend
basedpyright apps/backend

# Expected: 0 errors
```

**Configuration:**
```json
// File: pyrightconfig.json (if not exists)
{
  "include": [
    "apps/backend"
  ],
  "exclude": [
    "**/node_modules",
    "**/__pycache__",
    "**/venv"
  ],
  "typeCheckingMode": "basic",
  "pythonVersion": "3.12",
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "strictParameterNoneValue": true
}
```

##### 3.4 Remove Circular Import Warnings

**Audit Import Patterns:**

```bash
# Find all imports from apps.backend.services
grep -r "from apps.backend.services import" apps/backend --include="*.py" -n

# Expected: Should use specific submodules
# ✅ GOOD: from apps.backend.services.email import email_service
# ❌ BAD: from apps.backend.services import email_service
```

**Fix Remaining Circular Imports:**

```python
# File: scripts/fixes/fix_circular_imports.py

import re
from pathlib import Path

def fix_service_imports(file_path):
    """Fix circular import patterns in service imports."""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern: from apps.backend.services import email_service
    # Fix: from apps.backend.services.email import email_service
    content = re.sub(
        r'from apps\.backend\.services import email_service',
        'from apps.backend.services.email import email_service',
        content
    )

    # Pattern: from apps.backend.services import stripe_service
    # Fix: from apps.backend.services.stripe_service import stripe_service
    content = re.sub(
        r'from apps\.backend\.services import stripe_service',
        'from apps.backend.services.stripe_service import stripe_service',
        content
    )

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

# Run on all files
for py_file in Path('apps/backend').rglob('*.py'):
    if fix_service_imports(py_file):
        print(f"✅ Fixed imports in {py_file}")
```

#### Acceptance Criteria
- [ ] TypeError resolved - no errors in Render logs
- [ ] BasedPyright type checking passes with 0 errors
- [ ] All circular import warnings eliminated
- [ ] Code follows Python 3.12 type annotation best practices
- [ ] All imports use explicit submodule paths

---

### **Phase 4: Monitoring and Observability** 📊
**Priority:** MEDIUM
**Estimated Time:** 2-3 hours
**Dependencies:** Phase 1-2 complete

#### Objectives
1. Set up health check monitoring
2. Configure error tracking and alerting
3. Implement performance monitoring
4. Create operational dashboards

#### Step-by-Step Actions

##### 4.1 Health Check Monitoring

**UptimeRobot Configuration:**

```yaml
# Health Check Monitors to Create:

Monitor 1 - Primary Health Check:
  URL: https://toolboxai-backend-8j12.onrender.com/health
  Type: HTTP(s)
  Interval: 5 minutes
  Alert Contacts: team@toolboxai.com
  Alert Conditions:
    - Status code != 200
    - Response time > 5000ms
    - Keyword not found: "healthy" or "degraded"

Monitor 2 - API Documentation:
  URL: https://toolboxai-backend-8j12.onrender.com/docs
  Type: HTTP(s)
  Interval: 15 minutes
  Alert Conditions:
    - Status code != 200

Monitor 3 - OpenAPI Spec:
  URL: https://toolboxai-backend-8j12.onrender.com/openapi.json
  Type: HTTP(s)
  Interval: 15 minutes
  Alert Conditions:
    - Status code != 200
    - Response size < 1000 bytes
```

**Render Native Monitoring:**

```yaml
# Render Dashboard → toolboxai-backend-8j12 → Health & Alerts

Health Check Path: /health
Expected Status: 200
Failure Threshold: 3 consecutive failures
Alert Channel: Email + Slack (if configured)

Resource Alerts:
  - CPU > 80% for 5 minutes
  - Memory > 90% for 5 minutes
  - Disk > 85%
```

##### 4.2 Error Tracking with Sentry

**Sentry Integration:**

```python
# File: apps/backend/core/monitoring/sentry_config.py

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

def init_sentry():
    """Initialize Sentry error tracking."""
    sentry_dsn = os.getenv('SENTRY_DSN')
    environment = os.getenv('ENVIRONMENT', 'production')

    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% of profiling
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Filter out health check requests
            before_send=lambda event, hint: None if '/health' in event.get('request', {}).get('url', '') else event,
        )
        print(f"✅ Sentry initialized for {environment}")
    else:
        print("⚠️  SENTRY_DSN not configured - error tracking disabled")
```

**Add to main.py:**
```python
from apps.backend.core.monitoring.sentry_config import init_sentry

# Initialize Sentry (after FastAPI app creation)
init_sentry()
```

**Sentry Environment Variable:**
```bash
# Add to Render environment
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

##### 4.3 Performance Monitoring

**OpenTelemetry Integration (Already Configured):**

The backend already has OpenTelemetry instrumentation. Configure exporters:

```python
# File: apps/backend/core/monitoring/telemetry_config.py

import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def init_telemetry():
    """Initialize OpenTelemetry tracing."""
    otlp_endpoint = os.getenv('OTLP_ENDPOINT')  # e.g., Jaeger, Honeycomb

    if otlp_endpoint:
        provider = TracerProvider()
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint)
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        print(f"✅ OpenTelemetry exporting to {otlp_endpoint}")
    else:
        print("ℹ️  OTLP_ENDPOINT not set - using default trace provider")
```

**Prometheus Metrics (Already Instrumented):**

```bash
# Metrics endpoint is already available
curl https://toolboxai-backend-8j12.onrender.com/metrics

# Set up Prometheus scraping:
# 1. Deploy Prometheus instance (Docker or managed service)
# 2. Configure scrape target:

scrape_configs:
  - job_name: 'toolboxai-backend'
    scrape_interval: 30s
    static_configs:
      - targets: ['toolboxai-backend-8j12.onrender.com']
    metrics_path: '/metrics'
    scheme: 'https'
```

##### 4.4 Operational Dashboard

**Grafana Dashboard Setup:**

```yaml
# Dashboard Panels:

Panel 1 - System Health:
  - Service Status (healthy/degraded)
  - Uptime
  - Last Deployment Time

Panel 2 - Service Availability:
  - Database Connection (%)
  - Redis Connection (%)
  - Pusher Connection (%)
  - Agent System Status

Panel 3 - Request Metrics:
  - Requests per Second (RPS)
  - Response Time (p50, p95, p99)
  - Error Rate (%)
  - 2xx/4xx/5xx Status Codes

Panel 4 - Resource Usage:
  - CPU Usage (%)
  - Memory Usage (%)
  - Active Database Connections
  - Redis Memory Usage

Panel 5 - API Endpoint Performance:
  - Top 10 Slowest Endpoints
  - Top 10 Most Requested Endpoints
  - Endpoints with Errors

Panel 6 - Agent System:
  - Agent Pool Size
  - Active Agents
  - Agent Task Queue Length
  - Average Task Duration
```

**Dashboard JSON Export:**
```json
{
  "dashboard": {
    "title": "ToolBoxAI Backend Monitoring",
    "timezone": "browser",
    "panels": [
      {
        "title": "Health Status",
        "targets": [
          {
            "expr": "up{job=\"toolboxai-backend\"}",
            "legendFormat": "Backend Status"
          }
        ]
      }
    ]
  }
}
```

##### 4.5 Alert Rules

**Critical Alerts (Immediate Action Required):**

```yaml
Alert 1 - Service Down:
  Condition: Health check returns non-200 status for 3+ consecutive checks
  Channels: Email, Slack, PagerDuty
  Severity: CRITICAL

Alert 2 - Database Connection Failed:
  Condition: health.checks.database == false for 5+ minutes
  Channels: Email, Slack
  Severity: CRITICAL

Alert 3 - High Error Rate:
  Condition: Error rate > 5% for 5+ minutes
  Channels: Email, Slack
  Severity: HIGH

Alert 4 - Agent System Failure:
  Condition: Agent initialization fails or pool size = 0
  Channels: Email, Slack
  Severity: HIGH
```

**Warning Alerts (Monitor and Investigate):**

```yaml
Alert 5 - Slow Response Time:
  Condition: p95 response time > 1000ms for 10+ minutes
  Channels: Email
  Severity: MEDIUM

Alert 6 - High CPU Usage:
  Condition: CPU > 80% for 15+ minutes
  Channels: Email
  Severity: MEDIUM

Alert 7 - Memory Pressure:
  Condition: Memory > 85% for 10+ minutes
  Channels: Email
  Severity: MEDIUM
```

#### Acceptance Criteria
- [ ] Health check monitoring active with UptimeRobot or equivalent
- [ ] Sentry error tracking configured and receiving errors
- [ ] OpenTelemetry exporting traces (if OTLP endpoint configured)
- [ ] Prometheus metrics accessible at /metrics
- [ ] Grafana dashboard created with key metrics
- [ ] Alert rules configured for critical conditions
- [ ] Test alerts by simulating failures

---

### **Phase 5: Frontend Deployment** 🚀
**Priority:** HIGH
**Estimated Time:** 2-3 hours
**Dependencies:** Phase 1 complete

#### Objectives
1. Deploy React dashboard to Vercel
2. Configure frontend environment variables
3. Test frontend-backend integration
4. Verify end-to-end user flows

#### Step-by-Step Actions

##### 5.1 Prepare Frontend for Deployment

**Pre-Deployment Checklist:**

```bash
# 1. Build the dashboard locally to verify no errors
cd apps/dashboard
pnpm install
pnpm run build

# Expected: Build succeeds with no errors
# Check dist/ directory is created

# 2. Verify environment variable usage
grep -r "import.meta.env" src --include="*.tsx" --include="*.ts"

# 3. Create .env.production template
cat > .env.production.example << EOF
# Backend API URL (Render deployment)
VITE_API_URL=https://toolboxai-backend-8j12.onrender.com

# Clerk Authentication
VITE_CLERK_PUBLISHABLE_KEY=pk_live_xxx

# Pusher Real-Time
VITE_PUSHER_APP_KEY=xxx
VITE_PUSHER_CLUSTER=us2

# Environment
VITE_ENVIRONMENT=production
EOF

# 4. Update vite.config.ts for production
# Ensure build optimizations are enabled
```

**Vite Configuration for Production:**

```typescript
// File: apps/dashboard/vite.config.ts

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,  // Enable for error tracking
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'mantine-vendor': ['@mantine/core', '@mantine/hooks'],
          'clerk-vendor': ['@clerk/clerk-react'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,  // Increase if needed
  },
  server: {
    port: 5179,
    proxy: {
      '/api': {
        target: 'https://toolboxai-backend-8j12.onrender.com',
        changeOrigin: true,
      },
    },
  },
});
```

##### 5.2 Deploy to Vercel

**Method 1: Vercel CLI (Recommended)**

```bash
# 1. Install Vercel CLI
pnpm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy from dashboard directory
cd apps/dashboard
vercel --prod

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Select your team/account
# - Link to existing project? No (or Yes if already created)
# - Project name: toolboxai-dashboard
# - Directory: ./
# - Override settings? No
```

**Method 2: GitHub Integration**

```yaml
# File: vercel.json (in repository root)
{
  "version": 2,
  "builds": [
    {
      "src": "apps/dashboard/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://toolboxai-backend-8j12.onrender.com/api/$1"
    },
    {
      "handle": "filesystem"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "VITE_API_URL": "https://toolboxai-backend-8j12.onrender.com",
    "VITE_ENVIRONMENT": "production"
  }
}
```

**Steps:**
1. Push code to GitHub (main branch)
2. Go to vercel.com → Import Project
3. Select repository: ToolBoxAI-Solutions
4. Configure:
   - Framework Preset: Vite
   - Root Directory: apps/dashboard
   - Build Command: `pnpm run build`
   - Output Directory: dist
5. Add environment variables (see next section)
6. Deploy

##### 5.3 Configure Vercel Environment Variables

**Environment Variables to Add:**

```bash
# Navigate to: Vercel Dashboard → Project Settings → Environment Variables

# Backend API
VITE_API_URL=https://toolboxai-backend-8j12.onrender.com

# Clerk Authentication
VITE_CLERK_PUBLISHABLE_KEY=pk_live_xxx  # Get from Clerk dashboard

# Pusher Real-Time
VITE_PUSHER_APP_KEY=your-pusher-key     # Same as backend PUSHER_KEY
VITE_PUSHER_CLUSTER=us2                 # Same as backend PUSHER_CLUSTER

# Environment
VITE_ENVIRONMENT=production

# Optional - Sentry (Frontend Error Tracking)
VITE_SENTRY_DSN=https://xxx@sentry.io/xxx
VITE_SENTRY_ENVIRONMENT=production
```

**Set Environment Variables:**
1. Vercel Dashboard → toolboxai-dashboard → Settings → Environment Variables
2. Add each variable above
3. Set scope: Production, Preview, Development (as needed)
4. Save and redeploy

##### 5.4 Configure Backend CORS for Frontend

**Update Backend ALLOWED_ORIGINS:**

```bash
# Render Dashboard → toolboxai-backend-8j12 → Environment

# Add Vercel frontend URL to ALLOWED_ORIGINS
ALLOWED_ORIGINS=https://toolboxai-dashboard.vercel.app,https://toolboxai-dashboard-*.vercel.app

# If using custom domain:
ALLOWED_ORIGINS=https://app.toolboxai.com,https://toolboxai-dashboard.vercel.app

# Save and redeploy backend
```

**Verify CORS Configuration:**

```python
# File: apps/backend/core/config.py

# Ensure ALLOWED_ORIGINS is properly configured
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')

# In main.py, verify CORS middleware:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

##### 5.5 Test Frontend-Backend Integration

**Integration Test Checklist:**

```bash
# 1. Visit deployed frontend URL
open https://toolboxai-dashboard.vercel.app

# 2. Test authentication flow
# - Click "Sign In"
# - Should redirect to Clerk login
# - After login, should return to dashboard
# - User profile should load

# 3. Test API calls
# - Navigate to different pages
# - Check browser DevTools → Network tab
# - Verify API calls to backend succeed (200 status)
# - Check for CORS errors (should be none)

# 4. Test real-time features
# - Trigger Pusher event from backend
# - Verify frontend receives event
# - Check Pusher connection in DevTools → Network → WS

# 5. Test agent content generation
# - Navigate to content creation page
# - Submit content generation request
# - Verify loading state shows
# - Verify content appears when ready
```

**Automated E2E Test:**

```typescript
// File: tests/e2e/deployment-verification.spec.ts
// Run with: pnpm run test:e2e

import { test, expect } from '@playwright/test';

test.describe('Production Deployment', () => {
  const baseURL = 'https://toolboxai-dashboard.vercel.app';

  test('Homepage loads successfully', async ({ page }) => {
    await page.goto(baseURL);
    await expect(page).toHaveTitle(/ToolBoxAI/);
  });

  test('API health check succeeds', async ({ request }) => {
    const response = await request.get(`${baseURL}/api/health`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toMatch(/healthy|degraded/);
  });

  test('Authentication flow works', async ({ page }) => {
    await page.goto(`${baseURL}/sign-in`);
    // Clerk sign-in form should load
    await expect(page.locator('[data-clerk-id]')).toBeVisible();
  });

  test('Dashboard loads after auth', async ({ page }) => {
    // Assumes test user credentials
    await page.goto(`${baseURL}/dashboard`);
    // Should show dashboard or redirect to login
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');
  });
});
```

##### 5.6 Configure Custom Domain (Optional)

**Vercel Custom Domain Setup:**

```bash
# 1. Vercel Dashboard → Project → Settings → Domains

# 2. Add domain
Domain: app.toolboxai.com

# 3. Configure DNS (with your DNS provider)
Type: CNAME
Name: app
Value: cname.vercel-dns.com

# 4. Wait for DNS propagation (~5-60 minutes)

# 5. Vercel will automatically provision SSL certificate

# 6. Update ALLOWED_ORIGINS in backend
ALLOWED_ORIGINS=https://app.toolboxai.com

# 7. Update Clerk redirect URLs
# Clerk Dashboard → Configure → Paths
# Add: https://app.toolboxai.com/sign-in
#      https://app.toolboxai.com/sign-up
```

#### Acceptance Criteria
- [ ] Frontend successfully deployed to Vercel
- [ ] All environment variables configured correctly
- [ ] CORS configured - frontend can call backend APIs
- [ ] Authentication flow works end-to-end
- [ ] Real-time features (Pusher) working
- [ ] Agent content generation tested and working
- [ ] Custom domain configured (if applicable)
- [ ] No console errors in browser DevTools
- [ ] E2E tests passing

---

## 📊 Success Metrics

### Technical Metrics
- **Uptime:** > 99.5% (target: 99.9%)
- **Response Time:** p95 < 500ms, p99 < 1000ms
- **Error Rate:** < 1% (target: < 0.1%)
- **Build Time:** < 5 minutes
- **Deploy Time:** < 3 minutes

### Functional Metrics
- **API Endpoints:** 178/178 operational
- **Service Health:** All services connected (database, Redis, Pusher, agents)
- **Authentication:** 100% success rate for valid credentials
- **Content Generation:** Agent system initialization < 2 seconds

### Quality Metrics
- **Type Check:** 0 BasedPyright errors
- **Linting:** 0 critical linting errors
- **Test Coverage:** > 80% (maintain current coverage)
- **Security:** 0 critical/high vulnerabilities (Snyk/Dependabot)

---

## 🚧 Risk Management

### High-Risk Areas

1. **Database Connection Configuration**
   - **Risk:** Incorrect DATABASE_URL may cause service outage
   - **Mitigation:** Test in preview environment first, keep backup config
   - **Rollback:** Revert to previous environment variables

2. **CORS Misconfiguration**
   - **Risk:** Frontend unable to call backend APIs
   - **Mitigation:** Test with curl before frontend deployment
   - **Rollback:** Update ALLOWED_ORIGINS immediately

3. **Agent System Initialization**
   - **Risk:** Lazy init may cause first-request timeout
   - **Mitigation:** Implement health check prewarming
   - **Rollback:** N/A (non-critical feature)

### Rollback Procedures

```bash
# Backend Rollback (Render)
# 1. Render Dashboard → Deploys tab
# 2. Find previous successful deployment
# 3. Click "Rollback to this version"
# 4. Wait ~2 minutes for rollback completion

# Frontend Rollback (Vercel)
# 1. Vercel Dashboard → Deployments tab
# 2. Find previous successful deployment
# 3. Click "Promote to Production"
# 4. Instant rollback

# Environment Variables Rollback
# 1. Keep copy of working environment variables
# 2. Use Render/Vercel API to bulk update
# 3. Or manually revert in dashboard
```

---

## 📅 Timeline

### Phase 1: Environment Configuration
- **Duration:** 1-2 hours
- **Day 1, Morning**
- **Blocking:** No

### Phase 2: Testing and Verification
- **Duration:** 2-3 hours
- **Day 1, Afternoon**
- **Blocking:** Requires Phase 1 database/Pusher configuration

### Phase 3: Code Quality Improvements
- **Duration:** 3-4 hours
- **Day 2, Morning-Afternoon**
- **Blocking:** No (can be done in parallel with Phase 4)

### Phase 4: Monitoring and Observability
- **Duration:** 2-3 hours
- **Day 2, Afternoon**
- **Blocking:** No (can be done in parallel with Phase 3)

### Phase 5: Frontend Deployment
- **Duration:** 2-3 hours
- **Day 3, Morning**
- **Blocking:** Requires Phase 1 (CORS configuration)

**Total Estimated Time:** 10-15 hours across 3 days

---

## ✅ Final Checklist

### Pre-Deployment
- [ ] All code changes committed to Git
- [ ] Environment variables documented in .env.example
- [ ] Secrets secured (not in code)
- [ ] Tests passing locally

### Phase 1 Complete
- [ ] All Render environment variables configured
- [ ] Database connected (health check shows `database: true`)
- [ ] Pusher connected (health check shows `pusher: true`)
- [ ] Health endpoint returns `"status": "healthy"`

### Phase 2 Complete
- [ ] Agent system tested and operational
- [ ] Critical endpoints returning 2xx responses
- [ ] Authentication flow verified
- [ ] Real-time features tested

### Phase 3 Complete
- [ ] TypeError fixed
- [ ] BasedPyright type checking passes
- [ ] Circular imports eliminated
- [ ] Code quality improved

### Phase 4 Complete
- [ ] Health monitoring active
- [ ] Error tracking configured (Sentry)
- [ ] Metrics dashboard created (Grafana)
- [ ] Alerts configured

### Phase 5 Complete
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] CORS configured correctly
- [ ] End-to-end flows tested
- [ ] Custom domain configured (if applicable)

### Post-Deployment
- [ ] Documentation updated
- [ ] Team notified of deployment
- [ ] Monitoring verified for 24 hours
- [ ] Performance baseline established

---

## 📞 Support and Escalation

### Issue Escalation Path

**Level 1 - Self-Service:**
- Check this plan
- Review Render/Vercel logs
- Check health endpoint

**Level 2 - Documentation:**
- Review `/docs/08-operations/deployment/`
- Check `/docs/10-security/`
- Review error tracking (Sentry)

**Level 3 - Team Support:**
- Slack: #toolboxai-devops
- Email: devops@toolboxai.com

**Level 4 - Emergency:**
- PagerDuty: Critical production issues
- Contact: On-call engineer

---

## 📚 References

### Documentation
- [Render Deployment Guide](/docs/08-operations/deployment/render-deployment.md)
- [Vercel Deployment Guide](/docs/08-operations/deployment/vercel-deployment.md)
- [Environment Variables](/docs/10-security/ENV_FILES_DOCUMENTATION.md)
- [Monitoring Setup](/docs/08-operations/monitoring/)

### External Resources
- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)

---

**Document Version:** 1.0
**Last Updated:** November 13, 2025
**Next Review:** After Phase 5 completion
**Owner:** DevOps Team
