# Testing Excellence Agent Tasks

**Agent Role**: Testing Specialist - Achieve 80%+ test coverage
**Worktree**: parallel-worktrees/testing-excellence
**Branch**: feature/comprehensive-testing
**Port**: 8024
**Priority**: HIGH

---

## 🎯 PRIMARY MISSION

Achieve comprehensive test coverage (>80%) across backend, dashboard, and Roblox components with focus on quality over quantity.

---

## Phase 1: Test Coverage Analysis

### Task 1.1: Generate Coverage Reports
```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/Toolbox014/ToolboxAI-Solutions

# Backend coverage
pytest --cov=apps/backend --cov=database --cov-report=html --cov-report=json tests/

# Dashboard coverage
npm -w apps/dashboard run test:coverage

# Generate summary
cat > TEST_COVERAGE_REPORT.md << 'EOF'
# Test Coverage Report - October 2, 2025

## Current Coverage

### Backend (Python)
- **Overall**: XX%
- **apps/backend**: XX%
- **database**: XX%
- **core**: XX%

### Dashboard (TypeScript)
- **Overall**: XX%
- **Components**: XX%
- **Services**: XX%
- **Utils**: XX%

## Coverage Goals

- **Target**: 80% overall
- **Critical paths**: 95%
- **API endpoints**: 90%
- **UI components**: 75%

EOF
```

### Task 1.2: Identify Coverage Gaps
```bash
# Find files with <50% coverage
coverage json
python << 'EOF'
import json

with open('coverage.json') as f:
    data = json.load(f)

low_coverage = []
for file, stats in data['files'].items():
    if stats['summary']['percent_covered'] < 50:
        low_coverage.append((file, stats['summary']['percent_covered']))

low_coverage.sort(key=lambda x: x[1])
print("Files with <50% coverage:")
for file, pct in low_coverage[:20]:
    print(f"  {pct:.1f}% - {file}")
EOF
```

---

## Phase 2: Backend API Testing (Target: 90%)

### Task 2.1: Unit Tests for All API Endpoints (57 files)
```python
# Create test file for each endpoint file
# Pattern: tests/api/v1/test_[endpoint].py

# Example: tests/api/v1/test_uploads.py
import pytest
from fastapi.testclient import TestClient
from apps.backend.main import app

client = TestClient(app)

class TestUploadsEndpoint:
    """Test upload endpoints"""

    def test_single_file_upload(self, auth_headers):
        """Test single file upload"""
        files = {"file": ("test.txt", b"Hello World", "text/plain")}
        response = client.post("/api/v1/uploads", files=files, headers=auth_headers)
        assert response.status_code == 200
        assert "file_id" in response.json()

    def test_multipart_upload_initiate(self, auth_headers):
        """Test multipart upload initiation"""
        data = {"filename": "large.mp4", "file_size": 500_000_000}
        response = client.post("/api/v1/uploads/multipart", json=data, headers=auth_headers)
        assert response.status_code == 200
        assert "upload_id" in response.json()

    def test_upload_progress(self, auth_headers):
        """Test upload progress tracking"""
        upload_id = "test-upload-123"
        response = client.get(f"/api/v1/uploads/{upload_id}/progress", headers=auth_headers)
        assert response.status_code == 200
        assert "progress" in response.json()

    def test_upload_unauthorized(self):
        """Test upload without auth fails"""
        files = {"file": ("test.txt", b"Hello", "text/plain")}
        response = client.post("/api/v1/uploads", files=files)
        assert response.status_code == 401

# Create for all 57 endpoint files
```

### Task 2.2: Integration Tests for Workflows
```python
# tests/integration/test_payment_workflow.py
class TestPaymentWorkflow:
    """Test complete payment workflow"""

    def test_subscription_signup_flow(self, client, test_user):
        """Test user subscribing to plan"""
        # 1. Create subscription
        response = client.post("/api/v1/subscriptions", json={
            "plan_id": "premium_monthly",
            "payment_method_id": "pm_test_123"
        })
        assert response.status_code == 200

        # 2. Process payment
        sub_id = response.json()["subscription_id"]
        response = client.post(f"/api/v1/subscriptions/{sub_id}/process")
        assert response.status_code == 200

        # 3. Verify subscription active
        response = client.get(f"/api/v1/subscriptions/{sub_id}")
        assert response.json()["status"] == "active"

# tests/integration/test_content_generation.py
class TestContentGenerationWorkflow:
    """Test AI content generation workflow"""

    def test_generate_lesson_plan(self, client, auth_headers):
        """Test generating lesson plan"""
        # 1. Initiate generation
        response = client.post("/api/v1/content/generate", json={
            "type": "lesson_plan",
            "topic": "Python basics",
            "grade_level": "10"
        }, headers=auth_headers)

        # 2. Monitor progress
        task_id = response.json()["task_id"]
        # Wait for completion or use WebSocket

        # 3. Retrieve generated content
        response = client.get(f"/api/v1/content/{task_id}", headers=auth_headers)
        assert "lesson_plan" in response.json()
```

### Task 2.3: Database Tests
```python
# tests/database/test_models.py
class TestUserModel:
    """Test User model"""

    @pytest.mark.asyncio
    async def test_create_user(self, async_session):
        """Test user creation"""
        user = User(email="test@example.com", hashed_password="hashed")
        async_session.add(user)
        await async_session.commit()

        # Verify user created
        result = await async_session.execute(
            select(User).where(User.email == "test@example.com")
        )
        db_user = result.scalar_one()
        assert db_user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_user_relationships(self, async_session, test_user):
        """Test user relationships loading"""
        # Test courses relationship
        result = await async_session.execute(
            select(User).options(selectinload(User.courses)).where(User.id == test_user.id)
        )
        user = result.scalar_one()
        assert isinstance(user.courses, list)
```

---

## Phase 3: Dashboard Component Testing (Target: 75%)

### Task 3.1: Component Unit Tests
```typescript
// apps/dashboard/src/components/__tests__/Roblox3DButton.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Roblox3DButton } from '../roblox/Roblox3DButton';

describe('Roblox3DButton', () => {
  it('renders button with correct text', () => {
    render(<Roblox3DButton>Click Me</Roblox3DButton>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn();
    render(<Roblox3DButton onClick={handleClick}>Click</Roblox3DButton>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies correct 3D styling', () => {
    const { container } = render(<Roblox3DButton>Test</Roblox3DButton>);
    const button = container.querySelector('button');
    expect(button).toHaveStyle({ transform: 'perspective(600px)' });
  });
});

// Create tests for all 384 component files
```

### Task 3.2: Hook Tests
```typescript
// apps/dashboard/src/hooks/__tests__/usePusherEvents.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { usePusherEvents } from '../usePusherEvents';

describe('usePusherEvents', () => {
  it('subscribes to Pusher channel', async () => {
    const { result } = renderHook(() => usePusherEvents('test-channel'));

    await waitFor(() => {
      expect(result.current.isSubscribed).toBe(true);
    });
  });

  it('receives events from channel', async () => {
    const eventHandler = vi.fn();
    renderHook(() => usePusherEvents('test-channel', {
      'test-event': eventHandler
    }));

    // Simulate Pusher event
    mockPusher.trigger('test-channel', 'test-event', { data: 'test' });

    await waitFor(() => {
      expect(eventHandler).toHaveBeenCalledWith({ data: 'test' });
    });
  });
});
```

### Task 3.3: E2E Tests with Playwright
```typescript
// tests/e2e/auth-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('user can sign up', async ({ page }) => {
    await page.goto('http://localhost:5179/signup');

    await page.fill('input[name="email"]', 'newuser@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePass123!');

    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/dashboard/);
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('user can log in', async ({ page }) => {
    await page.goto('http://localhost:5179/login');

    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'TestPass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/dashboard/);
  });
});

// tests/e2e/lesson-management.spec.ts
test.describe('Lesson Management', () => {
  test('teacher can create lesson', async ({ page }) => {
    await page.goto('http://localhost:5179/lessons/create');

    await page.fill('input[name="title"]', 'Python Basics');
    await page.fill('textarea[name="description"]', 'Introduction to Python');
    await page.selectOption('select[name="gradeLevel"]', '10');

    await page.click('button[type="submit"]');

    await expect(page.locator('text=Lesson created successfully')).toBeVisible();
  });
});
```

---

## Phase 4: Roblox Lua Testing

### Task 4.1: Lua Script Validation
```lua
-- tests/roblox/test_main_server.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TestEZ = require(ReplicatedStorage.DevPackages.TestEZ)

return function()
    describe("Main Server Script", function()
        it("should initialize correctly", function()
            local success = pcall(function()
                require(script.Parent.Parent.Main)
            end)
            expect(success).to.equal(true)
        end)

        it("should connect to backend API", function()
            local apiService = require(script.Parent.Parent.services.APIService)
            local connected = apiService:checkConnection()
            expect(connected).to.equal(true)
        end)
    end)
end
```

---

## Phase 5: Performance & Load Testing

### Task 5.1: API Load Tests with Locust
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before starting tests"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def get_lessons(self):
        """Get lessons list"""
        self.client.get("/api/v1/lessons", headers=self.headers)

    @task(2)
    def get_dashboard(self):
        """Get dashboard data"""
        self.client.get("/api/v1/dashboard/metrics", headers=self.headers)

    @task(1)
    def create_content(self):
        """Generate content"""
        self.client.post("/api/v1/content/generate", json={
            "type": "quiz",
            "topic": "Math"
        }, headers=self.headers)

# Run: locust -f tests/performance/locustfile.py --host=http://localhost:8009
```

---

## Phase 6: Fix All TODOs/FIXMEs

### Task 6.1: Backend TODOs (65 items)
```bash
# List all TODOs
grep -rn "TODO\|FIXME\|XXX\|HACK" apps/backend --include="*.py" > backend-todos.txt

# Create GitHub issues for each
cat backend-todos.txt | while read line; do
  # Extract file, line, comment
  file=$(echo $line | cut -d: -f1)
  linenum=$(echo $line | cut -d: -f2)
  comment=$(echo $line | cut -d: -f3-)

  gh issue create --title "TODO: $comment" \
    --label "technical-debt" \
    --body "File: $file:$linenum\nComment: $comment"
done
```

### Task 6.2: Dashboard TODOs (14 items)
```bash
# Similar process for dashboard
grep -rn "TODO\|FIXME\|XXX\|HACK" apps/dashboard/src --include="*.ts" --include="*.tsx" > dashboard-todos.txt
```

---

## 🎯 SUCCESS CRITERIA

- [ ] Backend coverage: >80%
- [ ] Dashboard coverage: >75%
- [ ] All API endpoints tested (57 files)
- [ ] E2E tests covering critical flows
- [ ] Load tests passing (>1000 RPS)
- [ ] All 65 backend TODOs addressed
- [ ] All 14 dashboard TODOs addressed
- [ ] Test documentation complete

---

## 📊 DELIVERABLES

1. ✅ 500+ new test files
2. ✅ TEST_COVERAGE_REPORT.md
3. ✅ E2E test suite (Playwright)
4. ✅ Load test suite (Locust)
5. ✅ Roblox Lua tests
6. ✅ All TODOs resolved or documented

---

**Target**: 80% overall test coverage with 95% critical path coverage
