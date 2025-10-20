import { chromium, FullConfig } from '@playwright/test';
import path from 'path';
import fs from 'fs/promises';

/**
 * Global setup for Playwright E2E tests
 * Handles authentication, test data setup, and environment preparation
 */

async function globalSetup(config: FullConfig) {
  console.log('🎭 Starting Playwright global setup...');

  // Ensure test directories exist
  const dirs = [
    'test-results',
    'playwright-report',
    'e2e/snapshots',
    '.auth',
  ];

  for (const dir of dirs) {
    const dirPath = path.join(process.cwd(), dir);
    await fs.mkdir(dirPath, { recursive: true });
  }

  // Launch browser for authentication
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to login page
    const firstProject = config.projects?.[0];
    const baseURL = firstProject?.use?.baseURL || 'http://localhost:5179';
    await page.goto(`${baseURL}/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000); // Give React time to render

    // Check if backend is available (Docker container on port 8009)
    const apiURL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8009';
    console.log(`🐳 Checking Docker backend at ${apiURL}...`);

    const healthCheck = await page.request.get(`${apiURL}/health`).catch(() => null);

    if (!healthCheck || !healthCheck.ok()) {
      console.warn('⚠️ Backend API in Docker is not available. Some tests may fail.');
      console.log('   Make sure Docker containers are running:');
      console.log('   - Backend should be on port 8009');
      console.log('   - Dashboard should be on port 5179');
    } else {
      console.log('✅ Backend API is available in Docker container');
    }

    // Perform admin authentication and save state
    // Using demo credentials from Login.tsx
    const adminEmail = process.env.TEST_ADMIN_EMAIL || 'admin@toolboxai.com';
    const adminPassword = process.env.TEST_ADMIN_PASSWORD || 'Admin123!';

    // Try to log in as admin
    try {
      // Use Clerk-specific selectors - Clerk uses "identifier" instead of "email"
      await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill(adminEmail);
      await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill(adminPassword);
      await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();

      // Wait for successful login
      await page.waitForURL(/\/dashboard/, { timeout: 5000 });

      // Save authentication state
      await context.storageState({
        path: path.join(process.cwd(), '.auth', 'admin.json')
      });
      console.log('✅ Admin authentication state saved');
    } catch (error) {
      console.log('⚠️ Could not authenticate admin user. Tests will use mock authentication.');

      // Create mock auth state for development
      const mockAuthState = {
        cookies: [],
        origins: [
          {
            origin: baseURL,
            localStorage: [
              {
                name: 'auth_token',
                value: JSON.stringify({
                  access_token: 'mock-jwt-token',
                  user: {
                    id: '1',
                    email: adminEmail,
                    role: 'admin',
                    name: 'Test Admin',
                  },
                  expires_at: Date.now() + 3600000, // 1 hour
                }),
              },
            ],
          },
        ],
      };

      await fs.writeFile(
        path.join(process.cwd(), '.auth', 'admin.json'),
        JSON.stringify(mockAuthState, null, 2)
      );
    }

    // Create teacher auth state
    // Using demo credentials from Login.tsx
    const teacherEmail = process.env.TEST_TEACHER_EMAIL || 'jane.smith@school.edu';
    const teacherAuthState = {
      cookies: [],
      origins: [
        {
          origin: baseURL,
          localStorage: [
            {
              name: 'auth_token',
              value: JSON.stringify({
                access_token: 'mock-teacher-jwt-token',
                user: {
                  id: '2',
                  email: teacherEmail,
                  role: 'teacher',
                  name: 'Test Teacher',
                },
                expires_at: Date.now() + 3600000,
              }),
            },
          ],
        },
      ],
    };

    await fs.writeFile(
      path.join(process.cwd(), '.auth', 'teacher.json'),
      JSON.stringify(teacherAuthState, null, 2)
    );
    console.log('✅ Teacher authentication state saved');

    // Create student auth state
    // Using demo credentials from Login.tsx
    const studentEmail = process.env.TEST_STUDENT_EMAIL || 'alex.johnson@student.edu';
    const studentAuthState = {
      cookies: [],
      origins: [
        {
          origin: baseURL,
          localStorage: [
            {
              name: 'auth_token',
              value: JSON.stringify({
                access_token: 'mock-student-jwt-token',
                user: {
                  id: '3',
                  email: studentEmail,
                  role: 'student',
                  name: 'Test Student',
                },
                expires_at: Date.now() + 3600000,
              }),
            },
          ],
        },
      ],
    };

    await fs.writeFile(
      path.join(process.cwd(), '.auth', 'student.json'),
      JSON.stringify(studentAuthState, null, 2)
    );
    console.log('✅ Student authentication state saved');

  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }

  console.log('✅ Playwright global setup complete');
  console.log('');
}

export default globalSetup;
