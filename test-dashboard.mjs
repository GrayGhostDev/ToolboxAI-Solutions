#!/usr/bin/env node

/**
 * Dashboard End-to-End Test Script
 * Tests the ToolboxAI dashboard running on http://localhost:5179
 *
 * Usage: node test-dashboard.mjs
 */

import { chromium } from 'playwright';

const DASHBOARD_URL = 'http://localhost:5179';
const BACKEND_URL = 'http://127.0.0.1:8009';

async function testDashboard() {
  console.log('🎭 Starting Playwright Dashboard Tests\n');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  // Track console messages
  const consoleMessages = [];
  const errors = [];

  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push({ type: msg.type(), text });
    if (msg.type() === 'error') {
      errors.push(text);
    }
  });

  page.on('pageerror', err => {
    errors.push(`Page Error: ${err.message}`);
  });

  try {
    // Test 1: Load dashboard homepage
    console.log('📝 Test 1: Loading dashboard homepage...');
    await page.goto(DASHBOARD_URL, {
      waitUntil: 'networkidle',
      timeout: 60000
    });

    const title = await page.title();
    console.log(`   ✅ Page loaded: ${title}`);

    // Take screenshot
    await page.screenshot({ path: '/tmp/dashboard-home.png', fullPage: true });
    console.log('   📸 Screenshot saved: /tmp/dashboard-home.png');

    // Test 2: Check for React root
    console.log('\n📝 Test 2: Checking React app mounting...');
    const rootElement = await page.locator('#root').count();
    if (rootElement > 0) {
      console.log('   ✅ React root element found');
    } else {
      console.log('   ❌ React root element NOT found');
    }

    // Test 3: Wait for dashboard content to load
    console.log('\n📝 Test 3: Waiting for dashboard content...');
    try {
      // Wait for common dashboard elements (adjust selectors as needed)
      await page.waitForSelector('nav, [role="navigation"], header', { timeout: 10000 });
      console.log('   ✅ Navigation elements loaded');
    } catch (e) {
      console.log('   ⚠️  Navigation elements not found within 10s');
    }

    // Test 4: Check for sidebar/navigation
    console.log('\n📝 Test 4: Checking for sidebar navigation...');
    const navLinks = await page.locator('a, button').count();
    console.log(`   ℹ️  Found ${navLinks} clickable elements (links/buttons)`);

    // Test 5: Try to find Roblox Studio link using stable selector
    console.log('\n📝 Test 5: Looking for Roblox Studio navigation...');
    try {
      // Use data-testid for stable element selection (not affected by animations)
      const robloxLink = page.locator('[data-testid="nav-roblox-studio"]');

      // Wait for element to be visible
      await robloxLink.waitFor({ state: 'visible', timeout: 5000 });
      console.log('   ✅ Roblox Studio link found');

      // Click and navigate with force option to bypass animation checks
      console.log('   🖱️  Clicking Roblox Studio link...');
      await robloxLink.click({ force: true });
      await page.waitForLoadState('networkidle', { timeout: 30000 });

      const currentUrl = page.url();
      console.log(`   ✅ Navigated to: ${currentUrl}`);

      // Screenshot of Roblox Studio page
      await page.screenshot({ path: '/tmp/dashboard-roblox-studio.png', fullPage: true });
      console.log('   📸 Screenshot saved: /tmp/dashboard-roblox-studio.png');
    } catch (e) {
      console.log(`   ⚠️  Could not find or click Roblox Studio link: ${e.message}`);
    }

    // Test 6: Check backend connectivity
    console.log('\n📝 Test 6: Testing backend API connectivity...');
    try {
      const response = await page.request.get(`${BACKEND_URL}/health`);
      const healthData = await response.json();
      console.log('   ✅ Backend health check:', JSON.stringify(healthData, null, 2));
    } catch (e) {
      console.log(`   ❌ Backend connection failed: ${e.message}`);
    }

    // Test 7: Console errors summary
    console.log('\n📝 Test 7: Console Errors Summary');
    if (errors.length === 0) {
      console.log('   ✅ No console errors detected');
    } else {
      console.log(`   ⚠️  Found ${errors.length} console errors:`);
      errors.slice(0, 5).forEach((err, i) => {
        console.log(`      ${i + 1}. ${err.substring(0, 100)}...`);
      });
      if (errors.length > 5) {
        console.log(`      ... and ${errors.length - 5} more errors`);
      }
    }

    // Test 8: Page metrics
    console.log('\n📝 Test 8: Performance Metrics');
    const performanceMetrics = await page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: Math.round(perf.domContentLoadedEventEnd - perf.fetchStart),
        loadComplete: Math.round(perf.loadEventEnd - perf.fetchStart),
        domInteractive: Math.round(perf.domInteractive - perf.fetchStart)
      };
    });
    console.log('   ⏱️  DOM Content Loaded:', performanceMetrics.domContentLoaded, 'ms');
    console.log('   ⏱️  Page Load Complete:', performanceMetrics.loadComplete, 'ms');
    console.log('   ⏱️  DOM Interactive:', performanceMetrics.domInteractive, 'ms');

    // Final summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 TEST SUMMARY');
    console.log('='.repeat(60));
    console.log('Dashboard URL:', DASHBOARD_URL);
    console.log('Page Title:', title);
    console.log('Console Errors:', errors.length);
    console.log('Total Console Messages:', consoleMessages.length);
    console.log('Screenshots:', '/tmp/dashboard-*.png');
    console.log('='.repeat(60));

  } catch (error) {
    console.error('\n❌ Test failed with error:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
    console.log('\n✨ Tests complete!\n');
  }
}

// Run tests
testDashboard().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
