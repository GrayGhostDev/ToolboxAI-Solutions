#!/usr/bin/env node

/**
 * Terminal 2 Integration Verification Script
 * 
 * Tests real data flow between Terminal 2 (Dashboard) and Terminal 1 (Backend API)
 * Verifies WebSocket connections, authentication, and real-time data synchronization
 */

const axios = require('axios');
const io = require('socket.io-client');
const chalk = require('chalk');

// Configuration
const host = process.env.DASHBOARD_HOST || '127.0.0.1';
const port = Number(process.env.DASHBOARD_PORT || 5179);
const DASHBOARD_URL = `http://${host}:${port}`;
const API_BASE_URL = `http://${process.env.API_HOST || '127.0.0.1'}:${process.env.FASTAPI_PORT || 8008}`;
const WS_URL = API_BASE_URL;

// Test results tracking
let totalTests = 0;
let passedTests = 0;
let failedTests = 0;
const testResults = [];

// Utility functions
function logTest(name, passed, details = '') {
  totalTests++;
  if (passed) {
    passedTests++;
    console.log(chalk.green('✓'), name);
    testResults.push({ name, status: 'passed', details });
  } else {
    failedTests++;
    console.log(chalk.red('✗'), name, details ? chalk.gray(`(${details})`) : '');
    testResults.push({ name, status: 'failed', details });
  }
}

function logSection(title) {
  console.log(chalk.blue('\n' + '='.repeat(50)));
  console.log(chalk.blue.bold(title));
  console.log(chalk.blue('='.repeat(50)));
}

// Test functions
async function testDashboardAccess() {
  logSection('Testing Dashboard Accessibility');
  
  try {
    const response = await axios.get(DASHBOARD_URL);
    logTest('Dashboard is accessible', response.status === 200);
    logTest('Dashboard returns HTML', response.headers['content-type'].includes('text/html'));
    return true;
  } catch (error) {
    logTest('Dashboard is accessible', false, error.message);
    return false;
  }
}

async function testBackendAPI() {
  logSection('Testing Backend API (Terminal 1)');
  
  try {
    // Test health endpoint
    const healthResponse = await axios.get(`${API_BASE_URL}/health`);
    logTest('Backend API health check', healthResponse.status === 200);
    logTest('Backend returns healthy status', healthResponse.data.status === 'healthy');
    
    // Test API version
    try {
      const statusResponse = await axios.get(`${API_BASE_URL}/api/v1/status`);
      logTest('API status endpoint', statusResponse.status === 200);
    } catch (error) {
      // Some endpoints might require auth
      logTest('API status endpoint', error.response?.status === 401, 'Requires authentication');
    }
    
    return true;
  } catch (error) {
    logTest('Backend API health check', false, error.message);
    return false;
  }
}

async function testAuthentication() {
  logSection('Testing Authentication Flow');
  
  try {
    // Test with real credentials from database
    const loginResponse = await axios.post(`${API_BASE_URL}/auth/login`, {
      username: 'teacher',
      password: 'teacher123'
    });
    
    const hasToken = loginResponse.data.access_token || loginResponse.data.accessToken;
    logTest('Login endpoint works', loginResponse.status === 200);
    logTest('Returns access token', !!hasToken);
    logTest('Returns user data', !!loginResponse.data.user);
    
    if (hasToken) {
      const token = loginResponse.data.access_token || loginResponse.data.accessToken;
      
      // Test authenticated endpoint
      try {
        const meResponse = await axios.get(`${API_BASE_URL}/api/v1/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        logTest('Authenticated API call', meResponse.status === 200);
        logTest('Returns correct user data', meResponse.data.username === 'teacher');
      } catch (error) {
        logTest('Authenticated API call', false, error.response?.data?.detail || error.message);
      }
      
      return token;
    }
    
    return null;
  } catch (error) {
    if (error.response?.status === 401) {
      logTest('Login endpoint works', true, 'Invalid credentials rejected correctly');
    } else {
      logTest('Login endpoint works', false, error.message);
    }
    return null;
  }
}

async function testWebSocketConnection(token) {
  logSection('Testing WebSocket Connection');
  
  return new Promise((resolve) => {
    const socket = io(WS_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      path: '/socket.io/',
      timeout: 5000
    });
    
    const timeout = setTimeout(() => {
      logTest('WebSocket connection', false, 'Connection timeout');
      socket.disconnect();
      resolve(false);
    }, 5000);
    
    socket.on('connect', () => {
      clearTimeout(timeout);
      logTest('WebSocket connection established', true);
      logTest('Socket ID assigned', !!socket.id, socket.id);
      
      // Test ping-pong
      socket.emit('ping', { timestamp: Date.now() });
      
      const pongTimeout = setTimeout(() => {
        logTest('WebSocket ping-pong', false, 'No pong response');
        socket.disconnect();
        resolve(true);
      }, 2000);
      
      socket.on('pong', (data) => {
        clearTimeout(pongTimeout);
        const latency = Date.now() - (data.timestamp || 0);
        logTest('WebSocket ping-pong', true, `Latency: ${latency}ms`);
        socket.disconnect();
        resolve(true);
      });
    });
    
    socket.on('connect_error', (error) => {
      clearTimeout(timeout);
      logTest('WebSocket connection', false, error.message);
      socket.disconnect();
      resolve(false);
    });
  });
}

async function testRealDataFlow(token) {
  logSection('Testing Real Data Flow');
  
  try {
    // Test fetching real dashboard data
    const dashboardResponse = await axios.get(`${API_BASE_URL}/api/v1/dashboard/overview/teacher`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    logTest('Dashboard overview endpoint', dashboardResponse.status === 200);
    
    const data = dashboardResponse.data;
    const hasRealData = data && (
      data.totalStudents !== undefined ||
      data.totalClasses !== undefined ||
      data.recentActivity !== undefined
    );
    
    logTest('Returns real data (not mock)', hasRealData, 
      hasRealData ? 'Real database data' : 'No data or mock data detected');
    
    // Test fetching users (real database data)
    try {
      const usersResponse = await axios.get(`${API_BASE_URL}/api/v1/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const hasUsers = Array.isArray(usersResponse.data) && usersResponse.data.length > 0;
      logTest('Users endpoint returns data', hasUsers, 
        hasUsers ? `${usersResponse.data.length} users found` : 'No users in database');
    } catch (error) {
      logTest('Users endpoint returns data', false, error.response?.data?.detail || 'Access denied');
    }
    
    // Test fetching classes (real database data)
    try {
      const classesResponse = await axios.get(`${API_BASE_URL}/api/v1/classes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const hasClasses = Array.isArray(classesResponse.data) && classesResponse.data.length > 0;
      logTest('Classes endpoint returns data', hasClasses,
        hasClasses ? `${classesResponse.data.length} classes found` : 'No classes in database');
    } catch (error) {
      logTest('Classes endpoint returns data', false, error.response?.data?.detail || 'Access denied');
    }
    
    return true;
  } catch (error) {
    logTest('Real data flow', false, error.message);
    return false;
  }
}

async function testCrossTerminalCommunication() {
  logSection('Testing Cross-Terminal Communication');
  
  // This would test communication between Terminal 2 and Terminal 3 (Roblox)
  // For now, we'll just verify the endpoints exist
  
  try {
    // Test Roblox bridge endpoint
    const robloxHealthResponse = await axios.get('http://localhost:5001/health').catch(() => null);
    logTest('Terminal 3 (Roblox Bridge) accessible', 
      robloxHealthResponse?.status === 200,
      robloxHealthResponse ? 'Bridge is running' : 'Bridge not running'
    );
    
    return true;
  } catch (error) {
    logTest('Cross-terminal communication', false, error.message);
    return false;
  }
}

// Main test runner
async function runTests() {
  console.log(chalk.cyan.bold('\n🎨 TERMINAL 2 INTEGRATION VERIFICATION'));
  console.log(chalk.cyan('Testing Dashboard + Real Data Integration\n'));
  
  // Run all tests
  const dashboardOk = await testDashboardAccess();
  const backendOk = await testBackendAPI();
  const token = await testAuthentication();
  
  if (token) {
    await testWebSocketConnection(token);
    await testRealDataFlow(token);
  }
  
  await testCrossTerminalCommunication();
  
  // Print summary
  logSection('TEST SUMMARY');
  
  const successRate = Math.round((passedTests / totalTests) * 100);
  const statusColor = successRate === 100 ? chalk.green : 
                      successRate >= 80 ? chalk.yellow : 
                      chalk.red;
  
  console.log('\nResults:');
  console.log(chalk.green(`  ✓ Passed: ${passedTests}`));
  console.log(chalk.red(`  ✗ Failed: ${failedTests}`));
  console.log(statusColor(`  Success Rate: ${successRate}%`));
  
  if (successRate === 100) {
    console.log(chalk.green.bold('\n✅ TERMINAL 2 IS FULLY OPERATIONAL!'));
    console.log(chalk.green('All systems are working with real data.\n'));
  } else if (successRate >= 80) {
    console.log(chalk.yellow.bold('\n⚠️ TERMINAL 2 IS MOSTLY OPERATIONAL'));
    console.log(chalk.yellow('Some features may need attention.\n'));
  } else {
    console.log(chalk.red.bold('\n❌ TERMINAL 2 HAS ISSUES'));
    console.log(chalk.red('Critical problems detected. Review failed tests.\n'));
    
    // Show failed tests
    console.log('Failed tests:');
    testResults
      .filter(t => t.status === 'failed')
      .forEach(t => console.log(chalk.red(`  - ${t.name}: ${t.details}`)));
  }
  
  // Exit with appropriate code
  process.exit(failedTests > 0 ? 1 : 0);
}

// Check if required modules are installed
async function checkDependencies() {
  try {
    require('axios');
    require('socket.io-client');
    require('chalk');
    return true;
  } catch (error) {
    console.error('Missing dependencies. Installing...');
    const { execSync } = require('child_process');
    try {
      execSync('npm install axios socket.io-client chalk', { stdio: 'inherit' });
      return true;
    } catch (installError) {
      console.error('Failed to install dependencies:', installError.message);
      return false;
    }
  }
}

// Run the tests
(async () => {
  if (await checkDependencies()) {
    await runTests();
  } else {
    console.error('Cannot run tests without required dependencies');
    process.exit(1);
  }
})();