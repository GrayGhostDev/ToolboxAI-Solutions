// Performance Testing Script using k6
// Tests API endpoints, WebSocket connections, and system load handling

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const wsLatency = new Trend('ws_latency');
const contentGenTime = new Trend('content_generation_time');

// Test configuration
export const options = {
    scenarios: {
        // Scenario 1: API Load Test
        api_load: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 10 },  // Ramp up to 10 users
                { duration: '1m', target: 50 },   // Ramp up to 50 users
                { duration: '2m', target: 50 },   // Stay at 50 users
                { duration: '30s', target: 100 }, // Spike to 100 users
                { duration: '1m', target: 100 },  // Stay at 100 users
                { duration: '1m', target: 0 },    // Ramp down
            ],
            gracefulRampDown: '30s',
        },
        // Scenario 2: WebSocket Stress Test
        websocket_stress: {
            executor: 'constant-vus',
            vus: 20,
            duration: '3m',
            startTime: '1m', // Start after API test begins
        },
        // Scenario 3: Content Generation Load
        content_generation: {
            executor: 'per-vu-iterations',
            vus: 5,
            iterations: 10,
            maxDuration: '5m',
            startTime: '2m',
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% under 500ms, 99% under 1s
        http_req_failed: ['rate<0.1'],                   // Error rate under 10%
        ws_connecting: ['p(95)<1000'],                   // WebSocket connection under 1s
        errors: ['rate<0.1'],                            // Custom error rate under 10%
        api_latency: ['p(95)<500', 'p(99)<1000'],        // API latency thresholds
        content_generation_time: ['p(95)<10000'],        // Content gen under 10s
    },
};

// Configuration
const BASE_URL = __ENV.API_URL || 'http://127.0.0.1:8009';
const WS_URL = __ENV.WS_URL || 'ws://127.0.0.1:8009';

// Helper function to handle API responses
function handleResponse(response, endpoint) {
    const success = check(response, {
        [`${endpoint} status is 200`]: (r) => r.status === 200,
        [`${endpoint} has valid JSON`]: (r) => {
            try {
                JSON.parse(r.body);
                return true;
            } catch {
                return false;
            }
        },
    });

    errorRate.add(!success);
    apiLatency.add(response.timings.duration);

    return success;
}

// Scenario 1: API Load Test
export function api_load() {
    const endpoints = [
        '/health',
        '/api/v1/content/types',
        '/api/v1/agents/list',
        '/api/v1/auth/status',
    ];

    // Test each endpoint
    endpoints.forEach(endpoint => {
        const start = Date.now();
        const response = http.get(`${BASE_URL}${endpoint}`, {
            tags: { name: endpoint },
            timeout: '10s',
        });
        const duration = Date.now() - start;

        handleResponse(response, endpoint);

        // Log slow requests
        if (duration > 1000) {
            console.log(`Slow request: ${endpoint} took ${duration}ms`);
        }
    });

    // Test POST endpoints
    const authPayload = JSON.stringify({
        username: `testuser${__VU}`,
        password: 'testpass123',
    });

    const authResponse = http.post(`${BASE_URL}/api/v1/auth/login`, authPayload, {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'auth_login' },
        timeout: '10s',
    });

    if (authResponse.status === 200) {
        const token = JSON.parse(authResponse.body).access_token;

        // Test authenticated endpoints
        const authHeaders = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        };

        const profileResponse = http.get(`${BASE_URL}/api/v1/users/profile`, {
            headers: authHeaders,
            tags: { name: 'user_profile' },
        });

        handleResponse(profileResponse, 'user_profile');
    }

    sleep(1);
}

// Scenario 2: WebSocket Stress Test
export function websocket_stress() {
    const url = `${WS_URL}/ws/native`;

    const response = ws.connect(url, null, function (socket) {
        socket.on('open', () => {
            console.log(`VU ${__VU}: WebSocket connected`);

            // Send messages periodically
            for (let i = 0; i < 10; i++) {
                const start = Date.now();

                socket.send(JSON.stringify({
                    type: 'test_message',
                    vu_id: __VU,
                    iteration: i,
                    timestamp: new Date().toISOString(),
                }));

                socket.on('message', (data) => {
                    const latency = Date.now() - start;
                    wsLatency.add(latency);

                    check(data, {
                        'WebSocket message received': (d) => d !== null,
                        'WebSocket message valid': (d) => {
                            try {
                                JSON.parse(d);
                                return true;
                            } catch {
                                return false;
                            }
                        },
                    });
                });

                sleep(2);
            }

            socket.close();
        });

        socket.on('error', (e) => {
            console.log(`VU ${__VU}: WebSocket error: ${e}`);
            errorRate.add(1);
        });

        socket.setTimeout(() => {
            console.log(`VU ${__VU}: WebSocket timeout`);
            socket.close();
        }, 30000);
    });

    check(response, {
        'WebSocket connection successful': (r) => r && r.status === 101,
    });
}

// Scenario 3: Content Generation Load
export function content_generation() {
    const contentPayload = JSON.stringify({
        lesson_plan: {
            title: `Performance Test Lesson ${__VU}-${__ITER}`,
            subject: 'Mathematics',
            grade_level: 5,
            objectives: ['Learn addition', 'Practice multiplication'],
            content: 'Basic arithmetic operations',
        },
        config: {
            difficulty: 'medium',
            terrain_type: 'forest',
            include_quiz: true,
        },
    });

    const start = Date.now();

    const response = http.post(`${BASE_URL}/api/v1/content/generate`, contentPayload, {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'content_generation' },
        timeout: '30s',
    });

    const duration = Date.now() - start;
    contentGenTime.add(duration);

    const success = check(response, {
        'Content generation successful': (r) => r.status === 200 || r.status === 202,
        'Content generation response valid': (r) => {
            if (r.status !== 200 && r.status !== 202) return false;
            try {
                const body = JSON.parse(r.body);
                return body.task_id || body.content_id;
            } catch {
                return false;
            }
        },
    });

    if (!success) {
        errorRate.add(1);
        console.log(`Content generation failed: ${response.status} - ${response.body}`);
    } else {
        // Poll for completion if async
        if (response.status === 202) {
            const body = JSON.parse(response.body);
            const taskId = body.task_id;

            for (let i = 0; i < 10; i++) {
                sleep(2);

                const statusResponse = http.get(`${BASE_URL}/api/v1/content/status/${taskId}`, {
                    tags: { name: 'content_status' },
                });

                if (statusResponse.status === 200) {
                    const status = JSON.parse(statusResponse.body);
                    if (status.state === 'completed') {
                        console.log(`Content generation completed for task ${taskId}`);
                        break;
                    } else if (status.state === 'failed') {
                        console.log(`Content generation failed for task ${taskId}`);
                        errorRate.add(1);
                        break;
                    }
                }
            }
        }
    }

    sleep(1);
}

// Test MCP Agent Communication
export function test_mcp_agents() {
    const mcp_url = `${WS_URL}/ws/agent/content-agent`;

    const response = ws.connect(mcp_url, null, function (socket) {
        socket.on('open', () => {
            // Send agent task
            socket.send(JSON.stringify({
                type: 'task',
                action: 'generate_quiz',
                payload: {
                    topic: 'Mathematics',
                    difficulty: 'medium',
                    questions: 5,
                },
            }));

            socket.on('message', (data) => {
                check(data, {
                    'Agent response received': (d) => d !== null,
                    'Agent response valid': (d) => {
                        try {
                            const msg = JSON.parse(d);
                            return msg.type && msg.payload;
                        } catch {
                            return false;
                        }
                    },
                });
            });

            socket.setTimeout(() => {
                socket.close();
            }, 10000);
        });
    });

    check(response, {
        'MCP Agent connection successful': (r) => r && r.status === 101,
    });
}

// Handle test summary
export function handleSummary(data) {
    console.log('Test Summary:');
    console.log('=============');

    // Extract key metrics
    const metrics = {
        total_requests: data.metrics.http_reqs ? data.metrics.http_reqs.values.count : 0,
        failed_requests: data.metrics.http_req_failed ? data.metrics.http_req_failed.values.rate : 0,
        avg_duration: data.metrics.http_req_duration ? data.metrics.http_req_duration.values.avg : 0,
        p95_duration: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(95)'] : 0,
        p99_duration: data.metrics.http_req_duration ? data.metrics.http_req_duration.values['p(99)'] : 0,
        ws_connections: data.metrics.ws_connects ? data.metrics.ws_connects.values.count : 0,
        error_rate: data.metrics.errors ? data.metrics.errors.values.rate : 0,
    };

    console.log(`Total Requests: ${metrics.total_requests}`);
    console.log(`Failed Requests: ${(metrics.failed_requests * 100).toFixed(2)}%`);
    console.log(`Average Duration: ${metrics.avg_duration.toFixed(2)}ms`);
    console.log(`P95 Duration: ${metrics.p95_duration.toFixed(2)}ms`);
    console.log(`P99 Duration: ${metrics.p99_duration.toFixed(2)}ms`);
    console.log(`WebSocket Connections: ${metrics.ws_connections}`);
    console.log(`Error Rate: ${(metrics.error_rate * 100).toFixed(2)}%`);

    // Generate HTML report
    const htmlReport = `
<!DOCTYPE html>
<html>
<head>
    <title>Performance Test Report - ${new Date().toISOString()}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .metric { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #4CAF50; color: white; }
    </style>
</head>
<body>
    <h1>ToolBoxAI Performance Test Report</h1>
    <div class="metric">
        <h2>Summary</h2>
        <p>Test Duration: ${data.state.testRunDurationMs / 1000}s</p>
        <p>Total Requests: ${metrics.total_requests}</p>
        <p class="${metrics.failed_requests < 0.1 ? 'success' : 'error'}">
            Failed Requests: ${(metrics.failed_requests * 100).toFixed(2)}%
        </p>
        <p class="${metrics.error_rate < 0.1 ? 'success' : 'error'}">
            Error Rate: ${(metrics.error_rate * 100).toFixed(2)}%
        </p>
    </div>
    <div class="metric">
        <h2>Response Times</h2>
        <table>
            <tr><th>Metric</th><th>Value (ms)</th><th>Status</th></tr>
            <tr>
                <td>Average</td>
                <td>${metrics.avg_duration.toFixed(2)}</td>
                <td class="${metrics.avg_duration < 200 ? 'success' : 'warning'}">
                    ${metrics.avg_duration < 200 ? '✓' : '⚠'}
                </td>
            </tr>
            <tr>
                <td>P95</td>
                <td>${metrics.p95_duration.toFixed(2)}</td>
                <td class="${metrics.p95_duration < 500 ? 'success' : 'warning'}">
                    ${metrics.p95_duration < 500 ? '✓' : '⚠'}
                </td>
            </tr>
            <tr>
                <td>P99</td>
                <td>${metrics.p99_duration.toFixed(2)}</td>
                <td class="${metrics.p99_duration < 1000 ? 'success' : 'warning'}">
                    ${metrics.p99_duration < 1000 ? '✓' : '⚠'}
                </td>
            </tr>
        </table>
    </div>
    <div class="metric">
        <h2>WebSocket Performance</h2>
        <p>Total Connections: ${metrics.ws_connections}</p>
        <p>Average Latency: ${data.metrics.ws_latency ? data.metrics.ws_latency.values.avg.toFixed(2) : 'N/A'}ms</p>
    </div>
    <div class="metric">
        <h2>Content Generation</h2>
        <p>Average Time: ${data.metrics.content_generation_time ? (data.metrics.content_generation_time.values.avg / 1000).toFixed(2) : 'N/A'}s</p>
        <p>P95 Time: ${data.metrics.content_generation_time ? (data.metrics.content_generation_time.values['p(95)'] / 1000).toFixed(2) : 'N/A'}s</p>
    </div>
</body>
</html>
    `;

    // Return both console output and HTML report
    return {
        'stdout': JSON.stringify(metrics, null, 2),
        'performance_report.html': htmlReport,
        'performance_report.json': JSON.stringify(data, null, 2),
    };
}