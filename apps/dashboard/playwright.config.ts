import { defineConfig, devices } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

/**
 * Playwright Configuration for ToolBoxAI Dashboard
 * Comprehensive E2E testing setup with multiple browser configurations
 */

// ES module compatible __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Use Docker container ports
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5179';  // Dashboard in Docker
const apiURL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8009';    // Backend in Docker

export default defineConfig({
  // Test directory
  testDir: './e2e',

  // Test match pattern
  testMatch: '**/*.spec.ts',

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'test-results.xml' }],
    ['list'],
  ],

  // Shared settings for all projects
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL,

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Action timeout
    actionTimeout: 10 * 1000,

    // Navigation timeout
    navigationTimeout: 30 * 1000,

    // Test viewport
    viewport: { width: 1280, height: 720 },

    // Ignore HTTPS errors
    ignoreHTTPSErrors: true,

    // Extra HTTP headers
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },

    // Browser context options
    contextOptions: {
      // Accept downloads
      acceptDownloads: true,
      // Locale
      locale: 'en-US',
      // Timezone
      timezoneId: 'America/New_York',
      // Permissions (will be overridden per browser if needed)
      permissions: ['notifications'],
    },
  },

  // Configure projects for major browsers
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: ['--disable-blink-features=AutomationControlled']
        },
        contextOptions: {
          // Chromium supports clipboard permissions
          permissions: ['notifications', 'clipboard-read', 'clipboard-write'],
        }
      },
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        launchOptions: {
          firefoxUserPrefs: {
            // Allow third-party cookies and storage access
            'network.cookie.cookieBehavior': 0,
            'dom.security.https_first': false,
            'privacy.partition.network_state': false,
            // Disable tracking protection
            'privacy.trackingprotection.enabled': false,
            'privacy.trackingprotection.socialtracking.enabled': false,
            // Allow insecure connections for localhost
            'security.tls.insecure_fallback_hosts': 'localhost,127.0.0.1',
          }
        },
        // Longer timeouts for Firefox
        actionTimeout: 15 * 1000,
        navigationTimeout: 45 * 1000,
      },
    },
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
          ]
        },
        // WebKit-specific context options
        contextOptions: {
          ignoreHTTPSErrors: true,
          // WebKit handles cookies differently
          storageState: undefined,
        },
        // Longer timeouts for WebKit
        actionTimeout: 15 * 1000,
        navigationTimeout: 45 * 1000,
      },
    },

    // Mobile viewports
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },

    // Accessibility testing
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        // Force colors for accessibility testing
        colorScheme: 'dark',
      },
    },

    // API testing project
    {
      name: 'api',
      use: {
        // No browser needed for API tests
        baseURL: apiURL,
        extraHTTPHeaders: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      },
    },
  ],

  // Configure local dev server
  webServer: [
    {
      command: 'npm run dev',
      port: 5179,
      timeout: 120 * 1000,
      reuseExistingServer: true,  // Use already running server
      env: {
        VITE_API_BASE_URL: apiURL,
        VITE_WS_URL: `ws://localhost:8009`,
        VITE_ENABLE_WEBSOCKET: 'true',
        VITE_PUSHER_KEY: process.env.VITE_PUSHER_KEY || 'test-key',
        VITE_PUSHER_CLUSTER: process.env.VITE_PUSHER_CLUSTER || 'us2',
        VITE_E2E_TESTING: 'true',  // Disable auto-authentication for tests
      },
    },
  ],

  // Global setup and teardown
  globalSetup: path.join(__dirname, 'e2e', 'setup', 'global-setup.ts'),
  globalTeardown: path.join(__dirname, 'e2e', 'setup', 'global-teardown.ts'),

  // Timeout for each test
  timeout: 30 * 1000,

  // Expect timeout
  expect: {
    timeout: 5 * 1000,

    // Custom matchers
    toMatchSnapshot: { maxDiffPixels: 100 },
  },

  // Output folder for test artifacts
  outputDir: 'test-results/',

  // Folder for test artifacts such as screenshots, videos, traces, etc.
  snapshotDir: 'e2e/snapshots',

  // Path to global setup files
  globalTimeout: 10 * 60 * 1000, // 10 minutes
});