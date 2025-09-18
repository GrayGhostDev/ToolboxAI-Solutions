import { test as base, Page } from '@playwright/test';
import path from 'path';

/**
 * Authentication fixtures for different user roles
 */

export type UserRole = 'admin' | 'teacher' | 'student' | 'unauthenticated';

export interface AuthFixtures {
  authenticatedPage: Page;
  adminPage: Page;
  teacherPage: Page;
  studentPage: Page;
  userRole: UserRole;
}

export const test = base.extend<AuthFixtures>({
  // Default authenticated page (admin)
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'admin.json'),
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  // Admin authenticated page
  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'admin.json'),
    });
    const page = await context.newPage();

    // Add custom admin helpers
    page.isAdmin = () => true;
    page.waitForAdminDashboard = async () => {
      await page.waitForSelector('[data-testid="admin-dashboard"]', {
        state: 'visible',
        timeout: 10000,
      });
    };

    await use(page);
    await context.close();
  },

  // Teacher authenticated page
  teacherPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'teacher.json'),
    });
    const page = await context.newPage();

    page.isTeacher = () => true;
    page.waitForTeacherDashboard = async () => {
      await page.waitForSelector('[data-testid="teacher-dashboard"]', {
        state: 'visible',
        timeout: 10000,
      });
    };

    await use(page);
    await context.close();
  },

  // Student authenticated page
  studentPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.join(process.cwd(), '.auth', 'student.json'),
    });
    const page = await context.newPage();

    page.isStudent = () => true;
    page.waitForStudentDashboard = async () => {
      await page.waitForSelector('[data-testid="student-dashboard"]', {
        state: 'visible',
        timeout: 10000,
      });
    };

    await use(page);
    await context.close();
  },

  // User role fixture
  userRole: ['admin', { option: true }],
});

// Extend Page interface with custom methods
declare module '@playwright/test' {
  interface Page {
    isAdmin?: () => boolean;
    isTeacher?: () => boolean;
    isStudent?: () => boolean;
    waitForAdminDashboard?: () => Promise<void>;
    waitForTeacherDashboard?: () => Promise<void>;
    waitForStudentDashboard?: () => Promise<void>;
  }
}

export { expect } from '@playwright/test';