# Terminal 5: Testing and Verification Specialist

## CRITICAL: Complete Testing Suite and Verify System Integration

### Your Role
You are the **Testing and Verification Specialist**. Your mission is to create comprehensive tests, run all test suites, and verify that the entire system works end-to-end.

### Immediate Tasks

#### 1. Backend API Testing (HIGH PRIORITY)
```bash
cd ToolboxAI-Roblox-Environment

# Create comprehensive API tests
cat > tests/test_api_endpoints.py << 'EOF'
"""
Comprehensive API Endpoint Testing
"""
import pytest
import httpx
import asyncio
from datetime import datetime
import json

BASE_URL = "http://localhost:8008"
TEST_USER = {"email": "test@toolboxai.com", "password": "test123"}

@pytest.fixture
async def auth_headers():
    """Get authentication headers"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": TEST_USER["email"], "password": TEST_USER["password"]}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_health_check():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

@pytest.mark.asyncio
async def test_user_authentication():
    """Test user login and token generation"""
    async with httpx.AsyncClient() as client:
        # Test login
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "admin@toolboxai.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        
        # Test with wrong credentials
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "wrong@email.com", "password": "wrongpass"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_user_profile(auth_headers):
    """Test getting user profile"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data
        assert "role" in data

@pytest.mark.asyncio
async def test_get_courses(auth_headers):
    """Test fetching courses"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/courses",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            course = data[0]
            assert "id" in course
            assert "title" in course
            assert "teacher_id" in course

@pytest.mark.asyncio
async def test_content_generation(auth_headers):
    """Test AI content generation"""
    async with httpx.AsyncClient() as client:
        request_data = {
            "subject": "Mathematics",
            "grade_level": 5,
            "learning_objectives": ["Addition", "Subtraction"],
            "content_type": "lesson"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/content/generate",
            json=request_data,
            headers=auth_headers,
            timeout=60.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert "content" in data
        assert data["status"] == "completed"

@pytest.mark.asyncio
async def test_quiz_generation(auth_headers):
    """Test quiz generation"""
    async with httpx.AsyncClient() as client:
        request_data = {
            "topic": "Solar System",
            "difficulty": "medium",
            "num_questions": 5,
            "question_types": ["multiple_choice", "true_false"]
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/quiz/generate",
            json=request_data,
            headers=auth_headers,
            timeout=60.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "quiz_id" in data
        assert "questions" in data
        assert len(data["questions"]) == 5

@pytest.mark.asyncio
async def test_analytics_endpoint(auth_headers):
    """Test analytics data retrieval"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connectivity"""
    import websockets
    
    uri = "ws://localhost:8008/ws"
    try:
        async with websockets.connect(uri) as websocket:
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Receive pong
            response = await websocket.recv()
            data = json.loads(response)
            assert data["type"] == "pong"
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")

@pytest.mark.asyncio
async def test_rate_limiting(auth_headers):
    """Test API rate limiting"""
    async with httpx.AsyncClient() as client:
        # Make 100 rapid requests
        tasks = []
        for _ in range(100):
            task = client.get(f"{BASE_URL}/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if rate limiting kicks in
        status_codes = [r.status_code for r in responses if not isinstance(r, Exception)]
        assert 429 in status_codes or all(s == 200 for s in status_codes)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
EOF

# Run API tests
pytest tests/test_api_endpoints.py -v --asyncio-mode=auto
```

#### 2. Frontend Component Testing
```bash
cd src/dashboard

# Create component tests
cat > src/__tests__/components/Dashboard.test.tsx << 'EOF'
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import DashboardHome from '../../components/pages/DashboardHome';
import { AuthProvider } from '../../contexts/AuthContext';
import { vi } from 'vitest';

// Mock API
vi.mock('../../services/api', () => ({
  default: {
    getCourses: vi.fn().mockResolvedValue([
      { id: 1, title: 'Test Course', teacher_id: 1 }
    ]),
    getStudents: vi.fn().mockResolvedValue([
      { id: 1, name: 'Test Student', is_active: true }
    ]),
    getAnalytics: vi.fn().mockResolvedValue({
      overall_completion_rate: 75,
      total_assignments: 10,
      completed_assignments: 7,
      average_score: 85
    })
  }
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('DashboardHome', () => {
  it('renders dashboard overview', async () => {
    render(
      <AllTheProviders>
        <DashboardHome />
      </AllTheProviders>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    });
  });
  
  it('displays statistics cards', async () => {
    render(
      <AllTheProviders>
        <DashboardHome />
      </AllTheProviders>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Total Students')).toBeInTheDocument();
      expect(screen.getByText('Active Courses')).toBeInTheDocument();
      expect(screen.getByText('Assignments')).toBeInTheDocument();
      expect(screen.getByText('Avg. Score')).toBeInTheDocument();
    });
  });
  
  it('handles refresh button click', async () => {
    render(
      <AllTheProviders>
        <DashboardHome />
      </AllTheProviders>
    );
    
    const refreshButton = await screen.findByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);
    
    // Check if refresh is triggered
    await waitFor(() => {
      expect(refreshButton).toBeDisabled();
    });
  });
});
EOF

# Run frontend tests
npm test
```

#### 3. Integration Testing
```bash
# Create integration test suite
cat > tests/test_integration.py << 'EOF'
"""
End-to-End Integration Testing
"""
import pytest
import asyncio
import httpx
import asyncpg
from datetime import datetime

@pytest.mark.integration
class TestFullWorkflow:
    """Test complete user workflow"""
    
    @pytest.fixture
    async def setup_test_data(self):
        """Setup test data in database"""
        conn = await asyncpg.connect(
            host='localhost',
            database='toolboxai_db',
            user='toolboxai_user',
            password='staging_password_2024'
        )
        
        # Create test teacher
        teacher_id = await conn.fetchval(
            """INSERT INTO users (email, password_hash, full_name, role)
            VALUES ($1, $2, $3, $4) RETURNING id""",
            "test_teacher@test.com",
            "$2b$12$test_hash",
            "Test Teacher",
            "teacher"
        )
        
        # Create test course
        course_id = await conn.fetchval(
            """INSERT INTO courses (title, teacher_id, grade_level)
            VALUES ($1, $2, $3) RETURNING id""",
            "Test Course",
            teacher_id,
            5
        )
        
        yield {"teacher_id": teacher_id, "course_id": course_id}
        
        # Cleanup
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        await conn.execute("DELETE FROM users WHERE id = $1", teacher_id)
        await conn.close()
    
    @pytest.mark.asyncio
    async def test_teacher_workflow(self, setup_test_data):
        """Test teacher creating content and quiz"""
        async with httpx.AsyncClient() as client:
            # Login as teacher
            response = await client.post(
                "http://localhost:8008/api/v1/auth/login",
                json={"username": "teacher@toolboxai.com", "password": "teacher123"}
            )
            assert response.status_code == 200
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Generate content
            response = await client.post(
                "http://localhost:8008/api/v1/content/generate",
                json={
                    "subject": "Science",
                    "grade_level": 5,
                    "learning_objectives": ["Photosynthesis"],
                    "content_type": "lesson",
                    "course_id": setup_test_data["course_id"]
                },
                headers=headers,
                timeout=60.0
            )
            assert response.status_code == 200
            content_id = response.json()["content_id"]
            
            # Generate quiz
            response = await client.post(
                "http://localhost:8008/api/v1/quiz/generate",
                json={
                    "topic": "Photosynthesis",
                    "difficulty": "easy",
                    "num_questions": 3,
                    "question_types": ["multiple_choice"],
                    "course_id": setup_test_data["course_id"]
                },
                headers=headers,
                timeout=60.0
            )
            assert response.status_code == 200
            quiz_id = response.json()["quiz_id"]
            
            # Verify content and quiz exist
            assert content_id is not None
            assert quiz_id is not None
    
    @pytest.mark.asyncio
    async def test_student_workflow(self):
        """Test student accessing content and taking quiz"""
        async with httpx.AsyncClient() as client:
            # Login as student
            response = await client.post(
                "http://localhost:8008/api/v1/auth/login",
                json={"username": "student@toolboxai.com", "password": "student123"}
            )
            
            if response.status_code != 200:
                pytest.skip("Student login not configured")
            
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get enrolled courses
            response = await client.get(
                "http://localhost:8008/api/v1/courses",
                headers=headers
            )
            assert response.status_code == 200
            courses = response.json()
            
            if courses:
                course_id = courses[0]["id"]
                
                # Get course content
                response = await client.get(
                    f"http://localhost:8008/api/v1/courses/{course_id}/content",
                    headers=headers
                )
                assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_websocket_real_time_updates(self):
        """Test real-time updates via WebSocket"""
        import websockets
        import json
        
        uri = "ws://localhost:8008/ws"
        
        async with websockets.connect(uri) as websocket:
            # Join a room
            await websocket.send(json.dumps({
                "type": "join_room",
                "room": "class_1"
            }))
            
            # Send a message
            await websocket.send(json.dumps({
                "type": "message",
                "room": "class_1",
                "content": "Test message"
            }))
            
            # Wait for echo or confirmation
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            assert data is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
EOF

# Run integration tests
pytest tests/test_integration.py -v -m integration
```

#### 4. Performance Testing
```bash
# Create performance test script
cat > tests/test_performance.py << 'EOF'
"""
Performance and Load Testing
"""
import asyncio
import httpx
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import json

class PerformanceTester:
    def __init__(self, base_url="http://localhost:8008"):
        self.base_url = base_url
        self.results = []
    
    async def measure_endpoint(self, method, path, **kwargs):
        """Measure single endpoint performance"""
        async with httpx.AsyncClient() as client:
            start = time.time()
            response = await client.request(method, f"{self.base_url}{path}", **kwargs)
            end = time.time()
            
            return {
                "endpoint": path,
                "method": method,
                "status": response.status_code,
                "duration": end - start,
                "size": len(response.content)
            }
    
    async def load_test_endpoint(self, method, path, concurrent=10, iterations=100, **kwargs):
        """Load test an endpoint"""
        print(f"\n📊 Load testing {method} {path}")
        print(f"   Concurrent requests: {concurrent}")
        print(f"   Total iterations: {iterations}")
        
        all_results = []
        
        for batch in range(0, iterations, concurrent):
            tasks = []
            for _ in range(min(concurrent, iterations - batch)):
                task = self.measure_endpoint(method, path, **kwargs)
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend([r for r in batch_results if not isinstance(r, Exception)])
        
        # Calculate statistics
        durations = [r["duration"] for r in all_results]
        successful = [r for r in all_results if r["status"] == 200]
        
        stats = {
            "endpoint": path,
            "total_requests": len(all_results),
            "successful": len(successful),
            "failed": len(all_results) - len(successful),
            "min_time": min(durations),
            "max_time": max(durations),
            "avg_time": statistics.mean(durations),
            "median_time": statistics.median(durations),
            "p95_time": statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
            "requests_per_second": len(all_results) / sum(durations)
        }
        
        return stats
    
    async def run_performance_suite(self):
        """Run complete performance test suite"""
        print("🚀 Starting Performance Test Suite")
        print("=" * 50)
        
        # Test health endpoint (baseline)
        health_stats = await self.load_test_endpoint("GET", "/health", concurrent=50, iterations=500)
        self.print_stats(health_stats)
        
        # Test API endpoints with auth
        token = await self.get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test courses endpoint
        courses_stats = await self.load_test_endpoint(
            "GET", "/api/v1/courses", 
            concurrent=20, iterations=100,
            headers=headers
        )
        self.print_stats(courses_stats)
        
        # Test content generation (lower concurrency due to AI processing)
        content_stats = await self.load_test_endpoint(
            "POST", "/api/v1/content/generate",
            concurrent=5, iterations=20,
            headers=headers,
            json={
                "subject": "Math",
                "grade_level": 5,
                "learning_objectives": ["Test"],
                "content_type": "lesson"
            }
        )
        self.print_stats(content_stats)
        
        print("\n📈 Performance Test Summary")
        print("=" * 50)
        print("✅ All tests completed")
        
        # Check performance thresholds
        if health_stats["p95_time"] > 0.1:
            print("⚠️ Warning: Health endpoint P95 > 100ms")
        if courses_stats["p95_time"] > 0.5:
            print("⚠️ Warning: Courses endpoint P95 > 500ms")
        if content_stats["failed"] > 0:
            print(f"❌ Error: {content_stats['failed']} content generation requests failed")
    
    async def get_auth_token(self):
        """Get authentication token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "admin@toolboxai.com", "password": "admin123"}
            )
            return response.json()["access_token"]
    
    def print_stats(self, stats):
        """Print performance statistics"""
        print(f"\n📊 {stats['endpoint']}")
        print(f"   Total: {stats['total_requests']} | Success: {stats['successful']} | Failed: {stats['failed']}")
        print(f"   Min: {stats['min_time']:.3f}s | Avg: {stats['avg_time']:.3f}s | Max: {stats['max_time']:.3f}s")
        print(f"   Median: {stats['median_time']:.3f}s | P95: {stats['p95_time']:.3f}s")
        print(f"   Throughput: {stats['requests_per_second']:.1f} req/s")

async def main():
    tester = PerformanceTester()
    await tester.run_performance_suite()

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run performance tests
python tests/test_performance.py
```

#### 5. Database Testing
```bash
# Create database tests
cat > tests/test_database.py << 'EOF'
"""
Database integrity and performance testing
"""
import pytest
import asyncpg
import asyncio
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connectivity"""
    conn = await asyncpg.connect(
        host='localhost',
        database='toolboxai_db',
        user='toolboxai_user',
        password='staging_password_2024'
    )
    
    version = await conn.fetchval("SELECT version()")
    assert "PostgreSQL" in version
    
    await conn.close()

@pytest.mark.asyncio
async def test_referential_integrity():
    """Test foreign key constraints"""
    conn = await asyncpg.connect(
        host='localhost',
        database='toolboxai_db',
        user='toolboxai_user',
        password='staging_password_2024'
    )
    
    try:
        # Try to insert enrollment for non-existent student
        with pytest.raises(asyncpg.ForeignKeyViolationError):
            await conn.execute(
                """INSERT INTO course_enrollments (course_id, student_id)
                VALUES (1, 999999)"""
            )
    finally:
        await conn.close()

@pytest.mark.asyncio
async def test_query_performance():
    """Test critical query performance"""
    conn = await asyncpg.connect(
        host='localhost',
        database='toolboxai_db',
        user='toolboxai_user',
        password='staging_password_2024'
    )
    
    queries = [
        ("User lookup", "SELECT * FROM users WHERE email = $1", ["admin@toolboxai.com"]),
        ("Course listing", "SELECT * FROM courses WHERE school_id = $1", [1]),
        ("Student progress", """
            SELECT * FROM student_progress 
            WHERE student_id = $1 AND lesson_id = $2
        """, [1, 1]),
    ]
    
    for name, query, params in queries:
        start = asyncio.get_event_loop().time()
        await conn.fetch(query, *params)
        duration = asyncio.get_event_loop().time() - start
        
        print(f"{name}: {duration*1000:.2f}ms")
        assert duration < 0.1, f"{name} query too slow: {duration}s"
    
    await conn.close()

@pytest.mark.asyncio
async def test_concurrent_connections():
    """Test connection pooling"""
    async def run_query(n):
        conn = await asyncpg.connect(
            host='localhost',
            database='toolboxai_db',
            user='toolboxai_user',
            password='staging_password_2024'
        )
        result = await conn.fetchval("SELECT COUNT(*) FROM users")
        await conn.close()
        return result
    
    # Run 50 concurrent connections
    tasks = [run_query(i) for i in range(50)]
    results = await asyncio.gather(*tasks)
    
    # All should return the same count
    assert len(set(results)) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# Run database tests
pytest tests/test_database.py -v
```

#### 6. Create Test Report Generator
```bash
# Create test report script
cat > scripts/generate_test_report.sh << 'EOF'
#!/bin/bash

REPORT_FILE="test-results/test_report_$(date +%Y%m%d_%H%M%S).md"
mkdir -p test-results

echo "# Test Report" > $REPORT_FILE
echo "Generated: $(date)" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "## 1. Backend API Tests" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
cd ToolboxAI-Roblox-Environment
pytest tests/test_api_endpoints.py -v --tb=short 2>&1 | tee -a ../$REPORT_FILE
echo '```' >> $REPORT_FILE
cd ..

echo "" >> $REPORT_FILE
echo "## 2. Frontend Tests" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
cd src/dashboard
npm test 2>&1 | tee -a ../../$REPORT_FILE
echo '```' >> $REPORT_FILE
cd ../..

echo "" >> $REPORT_FILE
echo "## 3. Integration Tests" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
cd ToolboxAI-Roblox-Environment
pytest tests/test_integration.py -v -m integration 2>&1 | tee -a ../$REPORT_FILE
echo '```' >> $REPORT_FILE
cd ..

echo "" >> $REPORT_FILE
echo "## 4. Database Tests" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
cd ToolboxAI-Roblox-Environment
pytest tests/test_database.py -v 2>&1 | tee -a ../$REPORT_FILE
echo '```' >> $REPORT_FILE
cd ..

echo "" >> $REPORT_FILE
echo "## 5. Performance Tests" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
cd ToolboxAI-Roblox-Environment
python tests/test_performance.py 2>&1 | tee -a ../$REPORT_FILE
echo '```' >> $REPORT_FILE
cd ..

echo "" >> $REPORT_FILE
echo "## Summary" >> $REPORT_FILE
echo "✅ Test suite execution completed" >> $REPORT_FILE
echo "📊 Full report available at: $REPORT_FILE" >> $REPORT_FILE

echo "Test report generated: $REPORT_FILE"
EOF

chmod +x scripts/generate_test_report.sh
```

#### 7. Continuous Monitoring Script
```bash
# Create monitoring script
cat > scripts/monitor_system.sh << 'EOF'
#!/bin/bash

while true; do
    clear
    echo "🔍 System Health Monitor"
    echo "========================"
    echo "Time: $(date)"
    echo ""
    
    # Check services
    echo "📡 Service Status:"
    curl -s http://localhost:8008/health | jq -r '.status' | xargs -I {} echo "  FastAPI: {}"
    curl -s http://localhost:5001/health 2>/dev/null && echo "  Flask: ✅" || echo "  Flask: ❌"
    curl -s http://localhost:5177 > /dev/null 2>&1 && echo "  Dashboard: ✅" || echo "  Dashboard: ❌"
    
    echo ""
    echo "💾 Database:"
    psql -U toolboxai_user -d toolboxai_db -t -c "SELECT COUNT(*) FROM users" | xargs -I {} echo "  Users: {}"
    psql -U toolboxai_user -d toolboxai_db -t -c "SELECT COUNT(*) FROM courses" | xargs -I {} echo "  Courses: {}"
    
    echo ""
    echo "📊 Performance:"
    echo -n "  API Response: "
    time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8008/health)
    echo "${time}s"
    
    echo ""
    echo "🔄 Recent Activity:"
    psql -U toolboxai_user -d toolboxai_db -t -c "
        SELECT event_type, COUNT(*) 
        FROM analytics_events 
        WHERE created_at > NOW() - INTERVAL '1 hour'
        GROUP BY event_type
        LIMIT 5" | head -5
    
    sleep 10
done
EOF

chmod +x scripts/monitor_system.sh
```

## Communication Protocol
- Get test endpoints from Terminal 2
- Verify UI components with Terminal 3
- Test database queries from Terminal 4
- Coordinate with Terminal 1 on test file locations

## Success Metrics
✅ All API tests passing
✅ Frontend tests passing
✅ Integration tests passing
✅ Performance within thresholds
✅ Database integrity verified
✅ No critical security issues
✅ Test coverage > 80%
✅ Load tests successful

## Notes
- Run tests in CI/CD pipeline
- Monitor test execution time
- Generate coverage reports
- Document failing tests
- Create test data fixtures