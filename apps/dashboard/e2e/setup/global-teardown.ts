import type { FullConfig } from '@playwright/test';

/**
 * Global teardown for E2E tests
 * Runs once after all test files have finished
 */
async function globalTeardown(_config: FullConfig) {
  console.log('\n🧹 Running global teardown...');

  // Cleanup any test data if needed
  // This could include:
  // - Removing test users from database
  // - Cleaning up test files
  // - Stopping test servers

  console.log('✅ Global teardown complete\n');
}

export default globalTeardown;
