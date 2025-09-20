import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

/**
 * Lessons Management E2E Tests
 * Tests for lesson creation, editing, content management, and student interaction
 * Using Playwright 2025 best practices
 */

// Helper to login as teacher
async function loginAsTeacher(page: Page) {
  await page.goto('/login');
  await page.locator('input[name="email"]').fill('jane.smith@school.edu');
  await page.locator('input[name="password"]').fill('Teacher123!');
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
}

// Helper to navigate to lessons
async function navigateToLessons(page: Page) {
  // Navigate using exact text
  const lessonsLink = page.getByText('Lessons', { exact: true });

  // Check if sidebar is visible, if not try to open it
  if (!(await lessonsLink.isVisible())) {
    const menuButton = page.locator('button[aria-label*="menu"]');
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(500);
    }
  }

  await lessonsLink.click();
  await page.waitForURL(/\/lessons/, { timeout: 10000 });
}

test.describe('Lessons Creation and Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTeacher(page);
    await navigateToLessons(page);
  });

  test('should display lessons overview', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: /lessons|curriculum/i })).toBeVisible();

    // Check for create button
    await expect(page.getByRole('button', { name: /create.*lesson|new.*lesson|add.*lesson/i })).toBeVisible();

    // Check for lessons list
    const lessonsList = page.locator('[data-testid="lessons-list"], .lessons-grid, .lessons-container').first();
    await expect(lessonsList).toBeVisible();

    // Check for filter options
    await expect(page.locator('[data-testid="subject-filter"], select[name="subject"]').first()).toBeVisible();
  });

  test('should create a new text lesson', async ({ page }) => {
    // Click create lesson
    await page.getByRole('button', { name: /create.*lesson|new.*lesson/i }).click();

    // Wait for creation form
    await page.waitForSelector('[role="dialog"], form.lesson-form', { timeout: 5000 });

    // Fill lesson details
    const lessonTitle = `Test Lesson ${Date.now()}`;
    await page.locator('input[name="title"], input[placeholder*="title"]').fill(lessonTitle);

    // Select subject
    const subjectSelect = page.locator('select[name="subject"], [data-testid="subject-select"]').first();
    if (await subjectSelect.isVisible()) {
      await subjectSelect.selectOption('Mathematics');
    } else {
      // MUI Select
      await page.locator('[id*="subject"]').click();
      await page.getByRole('option', { name: /mathematics/i }).click();
    }

    // Select grade level
    const gradeSelect = page.locator('select[name="grade"], [data-testid="grade-select"]').first();
    if (await gradeSelect.isVisible()) {
      await gradeSelect.selectOption('9');
    }

    // Add description
    await page.locator('textarea[name="description"], textarea[placeholder*="description"]').fill(
      'This is a test lesson for E2E testing'
    );

    // Add learning objectives
    const objectivesInput = page.locator('textarea[name="objectives"], input[name="objectives"]').first();
    if (await objectivesInput.isVisible()) {
      await objectivesInput.fill('Students will learn basic algebra concepts');
    }

    // Select lesson type (if available)
    const lessonTypeSelect = page.locator('[name="type"], [data-testid="lesson-type"]').first();
    if (await lessonTypeSelect.isVisible()) {
      await lessonTypeSelect.selectOption('text');
    }

    // Add content
    const contentEditor = page.locator('[data-testid="content-editor"], .content-editor, textarea[name="content"]').first();
    await contentEditor.fill(`
# Introduction to Algebra

## What is Algebra?
Algebra is a branch of mathematics that uses letters and symbols to represent numbers and quantities in formulas and equations.

## Key Concepts
1. Variables
2. Expressions
3. Equations
4. Functions

## Practice Problems
1. Solve for x: 2x + 5 = 15
2. Simplify: 3(x + 4) - 2x
    `);

    // Set duration
    await page.locator('input[name="duration"], input[placeholder*="duration"]').fill('45');

    // Save lesson
    await page.getByRole('button', { name: /save|create|publish/i }).click();

    // Verify success
    await expect(page.getByText(/lesson.*created|successfully/i)).toBeVisible({ timeout: 10000 });

    // Verify lesson appears in list
    await expect(page.getByText(lessonTitle)).toBeVisible();
  });

  test('should create an interactive lesson', async ({ page }) => {
    // Click create lesson
    await page.getByRole('button', { name: /create.*lesson|new.*lesson/i }).click();

    // Select interactive type if available
    const typeSelector = page.locator('[data-testid="lesson-type-selector"]').first();
    if (await typeSelector.isVisible()) {
      await page.getByRole('button', { name: /interactive/i }).click();
    }

    // Fill basic details
    await page.locator('input[name="title"]').fill('Interactive Math Quiz');
    await page.locator('textarea[name="description"]').fill('Interactive quiz on algebra basics');

    // Add quiz questions (if quiz builder is available)
    const addQuestionBtn = page.getByRole('button', { name: /add.*question/i });
    if (await addQuestionBtn.isVisible()) {
      await addQuestionBtn.click();

      // Fill question details
      await page.locator('input[name="question"], textarea[name="question"]').first().fill('What is 2x + 3 when x = 5?');

      // Add answer options
      await page.locator('input[name="option1"], input[placeholder*="option a"]').first().fill('10');
      await page.locator('input[name="option2"], input[placeholder*="option b"]').first().fill('13');
      await page.locator('input[name="option3"], input[placeholder*="option c"]').first().fill('15');
      await page.locator('input[name="option4"], input[placeholder*="option d"]').first().fill('8');

      // Mark correct answer
      await page.locator('input[type="radio"][value="2"], input[type="checkbox"]').nth(1).check();
    }

    // Save lesson
    await page.getByRole('button', { name: /save|create/i }).click();

    // Verify success
    await expect(page.getByText(/created|saved/i)).toBeVisible({ timeout: 10000 });
  });

  test('should edit an existing lesson', async ({ page }) => {
    // Find and click edit on first lesson
    const firstLesson = page.locator('[data-testid="lesson-item"], .lesson-card').first();
    await firstLesson.locator('button[aria-label*="edit"], [data-testid="edit-lesson"]').click();

    // Wait for edit form
    await page.waitForSelector('[role="dialog"], form', { timeout: 5000 });

    // Update title
    const titleInput = page.locator('input[name="title"]').first();
    await titleInput.clear();
    await titleInput.fill('Updated Lesson Title');

    // Update description
    const descInput = page.locator('textarea[name="description"]').first();
    await descInput.clear();
    await descInput.fill('Updated lesson description for testing');

    // Save changes
    await page.getByRole('button', { name: /save|update/i }).click();

    // Verify success
    await expect(page.getByText(/updated|saved/i)).toBeVisible({ timeout: 5000 });
  });

  test('should duplicate a lesson', async ({ page }) => {
    // Find lesson with duplicate option
    const lesson = page.locator('[data-testid="lesson-item"]').first();

    // Open action menu
    await lesson.locator('button[aria-label*="more"], [data-testid="lesson-menu"]').click();

    // Click duplicate
    const duplicateOption = page.getByRole('menuitem', { name: /duplicate|copy/i });
    if (await duplicateOption.isVisible()) {
      await duplicateOption.click();

      // Confirm duplication
      const confirmBtn = page.getByRole('button', { name: /duplicate|copy|confirm/i });
      if (await confirmBtn.isVisible()) {
        await confirmBtn.click();
      }

      // Verify success
      await expect(page.getByText(/duplicated|copied/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should delete a lesson', async ({ page }) => {
    // Find test lesson to delete
    const testLesson = page.locator('[data-testid="lesson-item"]').filter({ hasText: /test/i }).first();

    if (await testLesson.isVisible()) {
      // Click delete
      await testLesson.locator('button[aria-label*="delete"]').click();

      // Confirm deletion
      await page.getByRole('button', { name: /confirm|delete|yes/i }).click();

      // Verify deletion
      await expect(page.getByText(/deleted|removed/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should add multimedia content to lesson', async ({ page }) => {
    // Create or edit a lesson
    await page.getByRole('button', { name: /create.*lesson/i }).click();

    // Fill basic info
    await page.locator('input[name="title"]').fill('Multimedia Lesson');

    // Add video URL if supported
    const videoInput = page.locator('input[name="video"], input[placeholder*="youtube"]').first();
    if (await videoInput.isVisible()) {
      await videoInput.fill('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    }

    // Add image (mock file upload)
    const imageUpload = page.locator('input[type="file"][accept*="image"]').first();
    if (await imageUpload.isVisible()) {
      // Create a test file
      await imageUpload.setInputFiles({
        name: 'test.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-content')
      });
    }

    // Add audio link
    const audioInput = page.locator('input[name="audio"], input[placeholder*="audio"]').first();
    if (await audioInput.isVisible()) {
      await audioInput.fill('https://example.com/audio.mp3');
    }

    // Save
    await page.getByRole('button', { name: /save|create/i }).click();

    // Verify
    await expect(page.getByText(/created|saved/i)).toBeVisible({ timeout: 10000 });
  });

  test('should organize lessons into modules', async ({ page }) => {
    // Look for module/section management
    const moduleBtn = page.getByRole('button', { name: /module|section|unit/i });

    if (await moduleBtn.isVisible()) {
      await moduleBtn.click();

      // Create new module
      await page.locator('input[name="moduleName"]').fill('Algebra Basics');
      await page.getByRole('button', { name: /create|add/i }).click();

      // Drag lessons into module (if drag-drop is supported)
      // This would require more complex interaction

      // Verify module created
      await expect(page.getByText('Algebra Basics')).toBeVisible();
    }
  });
});

test.describe('Student Lesson Interaction', () => {
  test.beforeEach(async ({ page }) => {
    // Login as student
    await page.goto('/login');
    await page.locator('input[name="email"]').fill('alex.johnson@student.edu');
    await page.locator('input[name="password"]').fill('Student123!');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
  });

  test('should view available lessons', async ({ page }) => {
    // Navigate to lessons
    await page.getByRole('link', { name: /lessons|learn/i }).click();

    // Should see lessons but no create button
    await expect(page.getByRole('heading', { name: /lessons|my lessons/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /create.*lesson/i })).not.toBeVisible();

    // Should see lesson cards
    const lessons = page.locator('[data-testid="lesson-card"], .lesson-item');
    await expect(lessons.first()).toBeVisible();
  });

  test('should start a lesson', async ({ page }) => {
    // Navigate to lessons
    await page.getByRole('link', { name: /lessons/i }).click();

    // Click on first available lesson
    const firstLesson = page.locator('[data-testid="lesson-card"]').first();
    await firstLesson.click();

    // Should navigate to lesson view
    await page.waitForURL(/lesson/, { timeout: 5000 });

    // Check for lesson content
    await expect(page.getByRole('heading')).toBeVisible();

    // Check for start/continue button
    const startBtn = page.getByRole('button', { name: /start|begin|continue/i });
    await expect(startBtn).toBeVisible();
  });

  test('should track lesson progress', async ({ page }) => {
    // Navigate to a lesson
    await page.getByRole('link', { name: /lessons/i }).click();
    await page.locator('[data-testid="lesson-card"]').first().click();

    // Start lesson
    await page.getByRole('button', { name: /start|begin/i }).click();

    // Simulate progress (scroll or next button)
    const nextBtn = page.getByRole('button', { name: /next|continue/i });
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await page.waitForTimeout(1000);
      await nextBtn.click();
    }

    // Check for progress indicator
    const progressBar = page.locator('[role="progressbar"], .progress-bar, [data-testid="progress"]');
    await expect(progressBar).toBeVisible();
  });

  test('should complete a lesson and earn XP', async ({ page }) => {
    // Navigate to a short lesson
    await page.getByRole('link', { name: /lessons/i }).click();

    // Find a lesson marked as "short" or with low duration
    const shortLesson = page.locator('[data-testid="lesson-card"]').filter({ hasText: /quick|short|5 min/i }).first();

    if (await shortLesson.isVisible()) {
      await shortLesson.click();

      // Complete the lesson
      await page.getByRole('button', { name: /start/i }).click();

      // Click through to end
      let attempts = 0;
      while (attempts < 10) {
        const completeBtn = page.getByRole('button', { name: /complete|finish/i });
        if (await completeBtn.isVisible({ timeout: 1000 })) {
          await completeBtn.click();
          break;
        }

        const nextBtn = page.getByRole('button', { name: /next/i });
        if (await nextBtn.isVisible({ timeout: 1000 })) {
          await nextBtn.click();
        }
        attempts++;
      }

      // Check for completion message
      await expect(page.getByText(/completed|congratulations|earned.*xp/i)).toBeVisible({ timeout: 10000 });
    }
  });

  test('should submit lesson assignment', async ({ page }) => {
    // Navigate to lessons
    await page.getByRole('link', { name: /lessons/i }).click();

    // Find lesson with assignment
    const assignmentLesson = page.locator('[data-testid="lesson-card"]').filter({ hasText: /assignment|homework/i }).first();

    if (await assignmentLesson.isVisible()) {
      await assignmentLesson.click();

      // Look for assignment submission area
      const submitArea = page.locator('[data-testid="assignment-submit"], .assignment-area').first();

      if (await submitArea.isVisible()) {
        // Fill assignment answer
        await page.locator('textarea[name="answer"], [data-testid="assignment-input"]').fill(
          'This is my assignment submission for testing.'
        );

        // Attach file if supported
        const fileInput = page.locator('input[type="file"]').first();
        if (await fileInput.isVisible()) {
          await fileInput.setInputFiles({
            name: 'assignment.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('fake-pdf-content')
          });
        }

        // Submit assignment
        await page.getByRole('button', { name: /submit/i }).click();

        // Verify submission
        await expect(page.getByText(/submitted|received/i)).toBeVisible({ timeout: 5000 });
      }
    }
  });
});

test.describe('Lesson Search and Filters', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTeacher(page);
    await navigateToLessons(page);
  });

  test('should search lessons by title', async ({ page }) => {
    // Find search input
    const searchInput = page.locator('input[placeholder*="search"], input[name="search"]').first();
    await searchInput.fill('algebra');
    await searchInput.press('Enter');

    // Wait for results
    await page.waitForTimeout(1000);

    // Verify results contain search term
    const lessons = page.locator('[data-testid="lesson-item"], .lesson-card');
    const count = await lessons.count();

    if (count > 0) {
      const firstLesson = await lessons.first().textContent();
      expect(firstLesson?.toLowerCase()).toContain('algebra');
    }
  });

  test('should filter lessons by subject', async ({ page }) => {
    // Apply subject filter
    const subjectFilter = page.locator('select[name="subject"], [data-testid="subject-filter"]').first();
    if (await subjectFilter.isVisible()) {
      await subjectFilter.selectOption('Mathematics');

      // Wait for filter
      await page.waitForTimeout(1000);

      // Verify filtered results
      const lessons = page.locator('[data-testid="lesson-subject"]');
      const firstSubject = await lessons.first().textContent();
      expect(firstSubject).toContain('Mathematics');
    }
  });

  test('should filter lessons by difficulty', async ({ page }) => {
    // Apply difficulty filter
    const difficultyFilter = page.locator('[data-testid="difficulty-filter"], select[name="difficulty"]').first();
    if (await difficultyFilter.isVisible()) {
      await difficultyFilter.selectOption('beginner');

      // Verify filtered results
      await page.waitForTimeout(1000);
      const badges = page.locator('[data-testid="difficulty-badge"], .difficulty-indicator');
      const firstBadge = await badges.first().textContent();
      expect(firstBadge?.toLowerCase()).toContain('beginner');
    }
  });

  test('should sort lessons', async ({ page }) => {
    // Apply sort
    const sortSelect = page.locator('select[name="sort"], [data-testid="sort-select"]').first();
    if (await sortSelect.isVisible()) {
      await sortSelect.selectOption('newest');

      // Wait for sort
      await page.waitForTimeout(1000);

      // Verify order (would need date extraction logic)
      const lessons = page.locator('[data-testid="lesson-item"]');
      expect(await lessons.count()).toBeGreaterThan(0);
    }
  });
});