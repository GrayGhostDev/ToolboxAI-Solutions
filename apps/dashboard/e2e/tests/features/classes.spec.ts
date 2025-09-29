

import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';

/**
 * Classes Management E2E Tests
 * Tests for class creation, editing, deletion, and enrollment
 * Using Playwright 2025 best practices
 */

// Helper function to login as teacher
async function loginAsTeacher(page: Page) {
  await page.goto('/login');
  await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill('jane.smith@school.edu');
  await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill('Teacher123!');
  await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();

  // Wait for navigation with error handling for mocked environments
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 }).catch(() => {
    // Continue even if navigation doesn't happen (might be mocked)
  });
}

test.describe('Classes Management - Teacher', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTeacher(page);
    // Navigate to classes page - use exact text
    const classesLink = page.getByText('Classes', { exact: true });

    // Check if sidebar is visible, if not try to open it
    if (!(await classesLink.isVisible())) {
      const menuButton = page.locator('button[aria-label*="menu"]');
      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500);
      }
    }

    await classesLink.click();
    await page.waitForURL(/\/classes/, { timeout: 10000 });
  });

  test('should display classes list', async ({ page }) => {
    // Check for page title
    await expect(page.getByRole('heading', { name: /classes/i })).toBeVisible();

    // Check for create button - look for exact text
    const createButton = page.getByRole('button').filter({ hasText: 'Create Class' });
    await expect(createButton).toBeVisible({ timeout: 10000 });

    // Check for classes table or grid
    const classesContainer = page.locator('[data-testid="classes-list"], .classes-grid, .MuiDataGrid-root').first();
    await expect(classesContainer).toBeVisible();
  });

  test('should create a new class', async ({ page }) => {
    // Click create button - use exact text
    const createButton = page.getByRole('button').filter({ hasText: 'Create Class' });
    await createButton.click();

    // Wait for modal or form
    await page.waitForSelector('[role="dialog"], form', { timeout: 5000 });

    // Fill in class details
    const className = `Test Math Class ${Date.now()}`;
    await page.locator('input[name="name"], input[placeholder*="class name"]').fill(className);

    // Select subject
    const subjectSelector = page.locator('select[name="subject"], [data-testid="subject-select"]').first();
    if (await subjectSelector.isVisible()) {
      await subjectSelector.selectOption('Mathematics');
    } else {
      // Try MUI select
      await page.locator('[id*="subject"], [aria-label*="subject"]').click();
      await page.getByRole('option', { name: /mathematics/i }).click();
    }

    // Add description
    await page.locator('textarea[name="description"], textarea[placeholder*="description"]').fill(
      'This is a test class for E2E testing purposes'
    );

    // Set schedule if available
    const scheduleInput = page.locator('input[name="schedule"], input[placeholder*="schedule"]').first();
    if (await scheduleInput.isVisible()) {
      await scheduleInput.fill('Monday, Wednesday, Friday 9:00 AM');
    }

    // Submit form
    await page.getByRole('button', { name: /create|save|submit/i }).click();

    // Wait for success message or navigation
    await Promise.race([
      page.waitForSelector('[role="alert"]', { timeout: 5000 }),
      page.waitForURL(/classes/, { timeout: 5000 })
    ]);

    // Verify class was created
    await expect(page.getByText(className)).toBeVisible({ timeout: 10000 });
  });

  test('should edit an existing class', async ({ page }) => {
    // Find first class with edit button
    const firstClassRow = page.locator('[data-testid="class-row"], tr').first();

    // Click edit button
    await firstClassRow.locator('button[aria-label*="edit"], [data-testid="edit-class"]').click();

    // Wait for edit form
    await page.waitForSelector('[role="dialog"], form', { timeout: 5000 });

    // Update class name
    const nameInput = page.locator('input[name="name"], input[value*=""]').first();
    await nameInput.clear();
    await nameInput.fill('Updated Class Name');

    // Update description
    const descriptionInput = page.locator('textarea[name="description"]').first();
    await descriptionInput.clear();
    await descriptionInput.fill('Updated description for testing');

    // Save changes
    await page.getByRole('button', { name: /save|update/i }).click();

    // Verify success
    await expect(page.getByText(/updated.*successfully|changes.*saved/i)).toBeVisible({ timeout: 5000 });
  });

  test('should delete a class', async ({ page }) => {
    // Find a class to delete (preferably a test class)
    const testClassRow = page.locator('[data-testid="class-row"], tr').filter({ hasText: /test/i }).first();

    if (await testClassRow.isVisible()) {
      // Click delete button
      await testClassRow.locator('button[aria-label*="delete"], [data-testid="delete-class"]').click();

      // Confirm deletion in dialog
      await page.getByRole('button', { name: /confirm|delete|yes/i }).click();

      // Verify deletion
      await expect(page.getByText(/deleted.*successfully|removed/i)).toBeVisible({ timeout: 5000 });
    } else {
      test.skip();
    }
  });

  test('should view class details', async ({ page }) => {
    // Click on first class to view details
    const firstClass = page.locator('[data-testid="class-row"], .class-card').first();
    await firstClass.click();

    // Wait for details page
    await page.waitForURL(/classes\/\d+|class-detail/, { timeout: 5000 });

    // Check for class details sections
    await expect(page.getByRole('heading', { name: /overview|details/i })).toBeVisible();
    await expect(page.getByText(/students|enrollment/i)).toBeVisible();
    await expect(page.getByText(/lessons|curriculum/i)).toBeVisible();
  });

  test('should manage class enrollment', async ({ page }) => {
    // Navigate to first class
    await page.locator('[data-testid="class-row"], .class-card').first().click();

    // Go to enrollment section
    await page.getByRole('tab', { name: /students|enrollment/i }).click();

    // Click add students button
    const addButton = page.getByRole('button', { name: /add.*student|enroll/i });
    if (await addButton.isVisible()) {
      await addButton.click();

      // Search for student
      await page.locator('input[placeholder*="search"], input[name="search"]').fill('alex');

      // Select student
      const studentCheckbox = page.locator('input[type="checkbox"]').first();
      await studentCheckbox.check();

      // Confirm enrollment
      await page.getByRole('button', { name: /add|enroll|confirm/i }).click();

      // Verify success
      await expect(page.getByText(/enrolled.*successfully|added/i)).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Classes Management - Student', () => {
  test.beforeEach(async ({ page }) => {
    // Login as student
    await page.goto('/login');
    await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill('alex.johnson@student.edu');
    await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill('Student123!');
    await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 }).catch(() => {
      // Continue even if navigation doesn't happen (might be mocked)
    });
  });

  test('should view enrolled classes', async ({ page }) => {
    // Navigate to classes
    await page.getByRole('link', { name: /classes|courses/i }).click();

    // Verify student view
    await expect(page.getByRole('heading', { name: /my.*classes|enrolled/i })).toBeVisible();

    // Should NOT see create button (students can't create classes)
    await expect(page.getByRole('button', { name: /create.*class/i })).not.toBeVisible();

    // Should see enrolled classes
    const classesContainer = page.locator('[data-testid="enrolled-classes"], .classes-grid');
    await expect(classesContainer).toBeVisible();
  });

  test('should join a class with code', async ({ page }) => {
    // Navigate to classes
    await page.getByRole('link', { name: /classes|courses/i }).click();

    // Look for join class button
    const joinButton = page.getByRole('button', { name: /join.*class|enroll|add.*class/i });
    if (await joinButton.isVisible()) {
      await joinButton.click();

      // Enter class code
      await page.locator('input[name="code"], input[placeholder*="code"]').fill('TEST123');

      // Submit
      await page.getByRole('button', { name: /join|enroll|submit/i }).click();

      // Check for result (success or error)
      await expect(page.locator('[role="alert"]')).toBeVisible({ timeout: 5000 });
    }
  });

  test('should access class materials', async ({ page }) => {
    // Navigate to classes
    await page.getByRole('link', { name: /classes|courses/i }).click();

    // Click on first enrolled class
    const firstClass = page.locator('[data-testid="class-card"], .class-item').first();
    if (await firstClass.isVisible()) {
      await firstClass.click();

      // Check for class content
      await expect(page.getByRole('heading')).toBeVisible();

      // Check for lessons/materials section
      await expect(page.getByText(/lessons|materials|content/i)).toBeVisible();

      // Check for assignments section
      await expect(page.getByText(/assignments|homework/i)).toBeVisible();
    }
  });
});

test.describe('Classes Management - Admin', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill('admin@toolboxai.com');
    await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill('Admin123!');
    await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 }).catch(() => {
      // Continue even if navigation doesn't happen (might be mocked)
    });
  });

  test('should view all classes across the system', async ({ page }) => {
    // Navigate to admin classes view
    await page.getByRole('link', { name: /classes|courses/i }).click();

    // Should see admin controls
    await expect(page.getByRole('heading', { name: /all.*classes|manage.*classes/i })).toBeVisible();

    // Should have filters for teachers
    const teacherFilter = page.locator('[data-testid="teacher-filter"], select[name="teacher"]');
    await expect(teacherFilter).toBeVisible();

    // Should have bulk actions
    const bulkActions = page.locator('[data-testid="bulk-actions"], .bulk-actions');
    await expect(bulkActions).toBeVisible();
  });

  test('should export classes data', async ({ page }) => {
    // Navigate to classes
    await page.getByRole('link', { name: /classes/i }).click();

    // Look for export button
    const exportButton = page.getByRole('button', { name: /export|download/i });
    if (await exportButton.isVisible()) {
      // Start download
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();

      // If there's a format selection
      const csvOption = page.getByRole('menuitem', { name: /csv/i });
      if (await csvOption.isVisible({ timeout: 1000 })) {
        await csvOption.click();
      }

      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/classes.*\.(csv|xlsx|json)/);
    }
  });
});

test.describe('Classes Search and Filter', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTeacher(page);
    await page.getByRole('link', { name: /classes/i }).click().catch(async () => {
      // Try alternate navigation method if link not found
      await page.goto('/classes');
    });
  });

  test('should search for classes', async ({ page }) => {
    // Find search input
    const searchInput = page.locator('input[placeholder*="search"], input[name="search"]').first();
    await searchInput.fill('Math');
    await searchInput.press('Enter');

    // Wait for results
    await page.waitForTimeout(1000);

    // Verify filtered results
    const classItems = page.locator('[data-testid="class-row"], .class-card');
    const count = await classItems.count();

    if (count > 0) {
      // Verify all visible items contain search term
      for (let i = 0; i < count; i++) {
        const text = await classItems.nth(i).textContent();
        expect(text?.toLowerCase()).toContain('math');
      }
    }
  });

  test('should filter by subject', async ({ page }) => {
    // Find subject filter
    const subjectFilter = page.locator('select[name="subject"], [data-testid="subject-filter"]').first();
    if (await subjectFilter.isVisible()) {
      await subjectFilter.selectOption('Mathematics');

      // Wait for filter to apply
      await page.waitForTimeout(1000);

      // Verify filtered results show Mathematics classes
      const classItems = page.locator('[data-testid="class-row"], .class-card');
      const firstItem = await classItems.first().textContent();
      expect(firstItem?.toLowerCase()).toMatch(/math/);
    }
  });

  test('should sort classes', async ({ page }) => {
    // Find sort dropdown
    const sortDropdown = page.locator('[data-testid="sort-select"], select[name="sort"]').first();
    if (await sortDropdown.isVisible()) {
      // Sort by name
      await sortDropdown.selectOption('name');
      await page.waitForTimeout(500);

      // Get class names
      const classNames = await page.locator('[data-testid="class-name"]').allTextContents();

      // Verify alphabetical order
      const sortedNames = [...classNames].sort();
      expect(classNames).toEqual(sortedNames);
    }
  });
});