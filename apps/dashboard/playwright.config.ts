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
      // Visual regression testing project
      testMatch: /.*\.(spec|visual)\.ts/,
    },

    // Visual regression testing only (Chromium)
    {
      name: 'visual-regression',
      use: {
        ...devices['Desktop Chrome'],
        // Specific settings for consistent visual testing
        viewport: { width: 1280, height: 720 },
        deviceScaleFactor: 1,
        hasTouch: false,
        isMobile: false,
        colorScheme: 'light',
      },
      testMatch: /.*\.visual\.spec\.ts/,
      retries: 0, // No retries for visual tests
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
        // Clerk auth: Enable if VITE_CLERK_PUBLISHABLE_KEY is set, otherwise disable
        VITE_ENABLE_CLERK_AUTH: process.env.VITE_CLERK_PUBLISHABLE_KEY ? 'true' : 'false',
        VITE_CLERK_PUBLISHABLE_KEY: process.env.VITE_CLERK_PUBLISHABLE_KEY || '',
        VITE_CLERK_SIGN_IN_URL: '/sign-in',
        VITE_CLERK_SIGN_UP_URL: '/sign-up',
        VITE_ENABLE_WEBSOCKET: 'false',   // Disable WebSocket - use Pusher
        VITE_BYPASS_AUTH: process.env.VITE_CLERK_PUBLISHABLE_KEY ? 'false' : 'true',  // Disable bypass if Clerk enabled
        VITE_USE_MOCK_DATA: process.env.VITE_CLERK_PUBLISHABLE_KEY ? 'false' : 'true',  // Disable mocks if Clerk enabled
        VITE_PUSHER_KEY: process.env.VITE_PUSHER_KEY || 'test-key',
        VITE_PUSHER_CLUSTER: process.env.VITE_PUSHER_CLUSTER || 'us2',
        VITE_PUSHER_AUTH_ENDPOINT: '/pusher/auth',
        VITE_E2E_TESTING: 'true',  // Enable E2E testing mode
      },
    },
  ],

  // Global setup and teardown
  // Temporarily disabled for debugging
  // globalSetup: path.join(__dirname, 'e2e', 'setup', 'global-setup.ts'),
  // globalTeardown: path.join(__dirname, 'e2e', 'setup', 'global-teardown.ts'),

  // Timeout for each test
  timeout: 30 * 1000,

  // Expect timeout
  expect: {
    timeout: 5 * 1000,

    // Visual regression settings
    toHaveScreenshot: {
      // Maximum number of pixels that can be different
      maxDiffPixels: 100,
      // Maximum ratio of pixels that can be different (0-1)
      maxDiffPixelRatio: 0.01,
      // Pixel comparison threshold (0-1)
      threshold: 0.2,
      // Animations: 'allow' | 'disabled'
      animations: 'disabled',
      // CSS animations and transitions
      caret: 'hide',
      // Scale factor for retina displays
      scale: 'css',
    },

    // Snapshot settings
    toMatchSnapshot: {
      maxDiffPixels: 100,
      threshold: 0.2,
    },
  },

  // Output folder for test artifacts
  outputDir: 'test-results/',

  // Folder for test artifacts such as screenshots, videos, traces, etc.
  snapshotDir: 'e2e/snapshots',

  // Path to global setup files
  globalTimeout: 10 * 60 * 1000, // 10 minutes
});