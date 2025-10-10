/**
 * Visual Regression Tests - Quiz Pages
 *
 * Tests visual consistency of quiz creation, taking,
 * and results pages including various question types.
 */

import { test, expect } from '@playwright/test';
import {
  captureFullPageSnapshot,
  captureComponentSnapshot,
  preparePageForVisualTesting,
  maskDynamicElements,
  captureStateSnapshots,
  testResponsiveSnapshots,
  STANDARD_VIEWPORTS,
} from '../utils/visual-testing';

test.describe('Quiz Pages - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Quiz library - initial load', async ({ page }) => {
    await page.goto('/quizzes');
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'quizzes-library-initial', {
      mask: masks,
      waitForTimeout: 1000,
    });
  });

  test('Quiz creation - initial load', async ({ page }) => {
    await page.goto('/quizzes/create');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'quizzes-create-initial');
  });

  test('Quiz creation - multiple choice question', async ({ page }) => {
    await page.goto('/quizzes/create');

    // Add question button
    const addQuestionBtn = page.getByRole('button', { name: /add question/i });

    if (await addQuestionBtn.isVisible()) {
      await addQuestionBtn.click();
      await page.waitForTimeout(500);

      const questionSection = page.locator('[data-testid="question"], .question').first();
      if (await questionSection.isVisible()) {
        await captureComponentSnapshot(questionSection, 'quizzes-multiple-choice-question');
      }
    }
  });

  test('Quiz creation - AI generation panel', async ({ page }) => {
    await page.goto('/quizzes/create');

    const aiButton = page.getByRole('button', { name: /generate|ai/i });

    if (await aiButton.isVisible()) {
      await aiButton.click();
      await page.waitForTimeout(500);

      await captureViewportSnapshot(page, 'quizzes-ai-generation-panel');
    }
  });

  test('Quiz taking - start screen', async ({ page }) => {
    await page.goto('/quizzes/1/take');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'quizzes-take-start-screen');
  });

  test('Quiz taking - question screen', async ({ page }) => {
    await page.goto('/quizzes/1/take');

    // Click start button
    const startButton = page.getByRole('button', { name: /start|begin/i });

    if (await startButton.isVisible()) {
      await startButton.click();
      await page.waitForTimeout(500);

      await captureFullPageSnapshot(page, 'quizzes-take-question-screen');
    }
  });

  test('Quiz taking - progress indicator', async ({ page }) => {
    await page.goto('/quizzes/1/take');

    const progressIndicator = page.locator('[data-testid="progress"], .progress').first();

    if (await progressIndicator.isVisible()) {
      await captureComponentSnapshot(progressIndicator, 'quizzes-progress-indicator');
    }
  });

  test('Quiz results - summary page', async ({ page }) => {
    await page.goto('/quizzes/1/results');
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'quizzes-results-summary', {
      mask: masks,
    });
  });

  test('Quiz results - score breakdown', async ({ page }) => {
    await page.goto('/quizzes/1/results');

    const scoreBreakdown = page.locator('[data-testid="score-breakdown"], .score-breakdown').first();

    if (await scoreBreakdown.isVisible()) {
      await captureComponentSnapshot(scoreBreakdown, 'quizzes-score-breakdown');
    }
  });

  test('Quiz - responsive views', async ({ page }) => {
    await page.goto('/quizzes');

    await testResponsiveSnapshots(page, 'quizzes-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
    ]);
  });
});
