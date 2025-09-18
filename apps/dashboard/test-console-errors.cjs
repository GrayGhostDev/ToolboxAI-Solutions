#!/usr/bin/env node
/**
 * Quick script to check if dashboard loads without console errors
 * Using Playwright to capture console messages
 */

const { chromium } = require('playwright');

async function checkDashboardConsole() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const errors = [];
  const warnings = [];
  const logs = [];

  // Capture console messages
  page.on('console', (msg) => {
    const text = msg.text();
    const type = msg.type();

    if (type === 'error') {
      errors.push(text);
      console.log(`❌ ERROR: ${text}`);
    } else if (type === 'warning') {
      // Filter out React DevTools and other benign warnings
      if (!text.includes('Download the React DevTools') &&
          !text.includes('Configuration warnings') &&
          !text.includes('No authentication token found')) {
        warnings.push(text);
        console.log(`⚠️  WARNING: ${text}`);
      }
    } else if (type === 'log' &&
              (text.includes('Subscribed to channel') ||
               text.includes('Pusher connected') ||
               text.includes('WebSocket'))) {
      logs.push(text);
      console.log(`📝 LOG: ${text}`);
    }
  });

  // Handle page errors
  page.on('pageerror', (error) => {
    errors.push(error.message);
    console.log(`❌ PAGE ERROR: ${error.message}`);
  });

  try {
    console.log('\n🚀 Loading dashboard at http://127.0.0.1:5179/...\n');
    await page.goto('http://127.0.0.1:5179/', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // Wait a bit for any async errors
    await page.waitForTimeout(5000);

    console.log('\n📊 Dashboard Console Report:');
    console.log('=' .repeat(50));
    console.log(`✅ Errors: ${errors.length}`);
    console.log(`⚠️  Warnings (filtered): ${warnings.length}`);
    console.log(`📝 WebSocket/Pusher logs: ${logs.length}`);
    console.log('=' .repeat(50));

    // Check for specific issues we fixed
    const multiplePublicSubs = logs.filter(log =>
      log.includes('Subscribed to channel: public')
    );
    console.log(`\n🔍 Multiple 'public' subscriptions: ${multiplePublicSubs.length}`);

    const webGLErrors = errors.filter(err =>
      err.includes('WebGL') || err.includes('Too many active')
    );
    console.log(`🎨 WebGL context errors: ${webGLErrors.length}`);

    const jwtErrors = logs.filter(log =>
      log.includes('Invalid JWT token format')
    );
    console.log(`🔐 JWT validation errors: ${jwtErrors.length}`);

    const success = errors.length === 0 && multiplePublicSubs.length <= 1;

    console.log('\n' + (success ? '✅ Dashboard loads without critical errors!' : '❌ Dashboard has errors that need fixing'));

    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error('Failed to load dashboard:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

checkDashboardConsole().catch(console.error);