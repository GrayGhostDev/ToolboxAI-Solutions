/**
 * k6 Load Testing Script for ToolBoxAI
 *
 * This script performs comprehensive load testing including:
 * - API endpoint performance
 * - WebSocket connections
 * - Database query performance
 * - Concurrent user simulation
 *
 * Usage:
 * k6 run tests/performance/load-test.js
 * k6 run --vus 100 --duration 30s tests/performance/load-test.js
 */

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiDuration = new Trend('api_duration');
const wsConnections = new Counter('websocket_connections');
const dbQueryTime = new Trend('database_query_time');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp up to 20 users
    { duration: '1m', target: 50 },    // Ramp up to 50 users
    { duration: '2m', target: 100 },   // Stay at 100 users
    { duration: '1m', target: 50 },    // Ramp down to 50 users
    { duration: '30s', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests under 500ms
    errors: ['rate<0.1'],                            // Error rate under 10%
    websocket_connections: ['count>0'],              // At least 1 WS connection
    api_duration: ['p(95)<300'],                     // API 95th percentile under 300ms
  },
  ext: {
    loadimpact: {
      projectID: 'toolboxai',
      name: 'ToolBoxAI Load Test',
    },
  },
};

// Base URL configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8009';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8009';

// Test data
const testUser = {
  username: 'loadtest_user_' + Math.random(),
  password: 'Test123!@#',
  email: `loadtest_${Math.random()}@example.com`,
};

/**
 * Setup function - runs once before the test
 */
export function setup() {
  // Register test user
  const registerRes = http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify({
      username: testUser.username,
      email: testUser.email,
      password: testUser.password,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  // Login to get token
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({
      username: testUser.username,
      password: testUser.password,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  const authToken = loginRes.json('access_token');

  return { authToken };
}

/**
 * Main test function - runs for each virtual user
 */
export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.authToken}`,
  };

  // Test 1: Health Check
  const healthRes = http.get(`${BASE_URL}/api/v1/health`);
  check(healthRes, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  });
  errorRate.add(healthRes.status !== 200);

  // Test 2: Get Content List
  const startTime = Date.now();
  const contentRes = http.get(`${BASE_URL}/api/v1/content`, { headers });
  const duration = Date.now() - startTime;

  apiDuration.add(duration);
  check(contentRes, {
    'content list status is 200': (r) => r.status === 200,
    'content list has data': (r) => JSON.parse(r.body).data !== undefined,
    'content response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(contentRes.status !== 200);

  // Test 3: Create Content
  const createContentRes = http.post(
    `${BASE_URL}/api/v1/content`,
    JSON.stringify({
      title: `Load Test Content ${Date.now()}`,
      content: 'This is a load test content item',
      subject: 'Mathematics',
      grade_level: 5,
    }),
    { headers }
  );

  check(createContentRes, {
    'content creation status is 201': (r) => r.status === 201,
    'content creation returns ID': (r) => JSON.parse(r.body).data?.id !== undefined,
  });
  errorRate.add(createContentRes.status !== 201);

  // Test 4: Search Content
  const searchRes = http.get(
    `${BASE_URL}/api/v1/content/search?q=mathematics`,
    { headers }
  );

  check(searchRes, {
    'search status is 200': (r) => r.status === 200,
    'search returns results': (r) => JSON.parse(r.body).data !== undefined,
  });

  // Test 5: Database-heavy operation
  const dbStartTime = Date.now();
  const assessmentRes = http.get(
    `${BASE_URL}/api/v1/assessments?limit=100`,
    { headers }
  );
  dbQueryTime.add(Date.now() - dbStartTime);

  check(assessmentRes, {
    'database query status is 200': (r) => r.status === 200,
    'database query time < 1000ms': (r) => r.timings.duration < 1000,
  });

  // Test 6: Concurrent agent execution
  const agentRes = http.post(
    `${BASE_URL}/api/v1/agents/execute`,
    JSON.stringify({
      task: 'generate_quiz',
      parameters: {
        subject: 'Science',
        grade_level: 7,
        num_questions: 5,
      },
    }),
    { headers }
  );

  check(agentRes, {
    'agent execution initiated': (r) => r.status === 202 || r.status === 200,
  });

  // Test 7: WebSocket connection
  const wsResponse = ws.connect(`${WS_URL}/ws/content`, {}, function (socket) {
    socket.on('open', () => {
      wsConnections.add(1);
      socket.send(JSON.stringify({ type: 'ping' }));
    });

    socket.on('message', (data) => {
      check(data, {
        'websocket message received': (d) => d !== undefined,
      });
    });

    socket.on('error', (e) => {
      errorRate.add(1);
      console.error('WebSocket error:', e);
    });

    // Keep connection open for a bit
    sleep(2);
    socket.close();
  });

  // Simulate user think time
  sleep(Math.random() * 3 + 1);
}

/**
 * Teardown function - runs once after the test
 */
export function teardown(data) {
  // Clean up test user
  // Note: In a real scenario, you'd implement a cleanup endpoint
  console.log('Test completed. Cleanup may be required.');
}

/**
 * Handle summary generation
 */
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'performance-report.json': JSON.stringify(data),
    'performance-report.html': htmlReport(data),
  };
}

// Helper function for text summary
function textSummary(data, options) {
  const { metrics } = data;
  let summary = '\n=== Performance Test Results ===\n\n';

  // Request metrics
  summary += 'HTTP Requests:\n';
  summary += `  Total: ${metrics.http_reqs?.values?.count || 0}\n`;
  summary += `  Rate: ${metrics.http_reqs?.values?.rate?.toFixed(2) || 0} req/s\n`;
  summary += `  Duration p(95): ${metrics.http_req_duration?.values?.['p(95)']?.toFixed(2) || 0}ms\n`;
  summary += `  Duration p(99): ${metrics.http_req_duration?.values?.['p(99)']?.toFixed(2) || 0}ms\n\n`;

  // Custom metrics
  summary += 'Custom Metrics:\n';
  summary += `  Error Rate: ${(metrics.errors?.values?.rate * 100)?.toFixed(2) || 0}%\n`;
  summary += `  API Duration p(95): ${metrics.api_duration?.values?.['p(95)']?.toFixed(2) || 0}ms\n`;
  summary += `  DB Query Time p(95): ${metrics.database_query_time?.values?.['p(95)']?.toFixed(2) || 0}ms\n`;
  summary += `  WebSocket Connections: ${metrics.websocket_connections?.values?.count || 0}\n\n`;

  // Threshold results
  summary += 'Thresholds:\n';
  for (const [metric, passed] of Object.entries(metrics)) {
    if (metric.thresholds) {
      summary += `  ${metric}: ${passed ? '✓ PASS' : '✗ FAIL'}\n`;
    }
  }

  return summary;
}

// Helper function for HTML report
function htmlReport(data) {
  const html = `
<!DOCTYPE html>
<html>
<head>
  <title>ToolBoxAI Performance Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    .metric { margin: 10px 0; padding: 10px; border-left: 3px solid #4CAF50; }
    .fail { border-left-color: #f44336; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #4CAF50; color: white; }
  </style>
</head>
<body>
  <h1>ToolBoxAI Performance Test Report</h1>
  <div class="metrics">
    ${JSON.stringify(data.metrics, null, 2)}
  </div>
</body>
</html>
  `;
  return html;
}