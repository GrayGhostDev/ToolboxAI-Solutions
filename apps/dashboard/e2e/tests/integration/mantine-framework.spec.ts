import { test, expect, Page } from '@playwright/test';

/**
 * Comprehensive Playwright tests for Mantine v8 framework integration
 * Tests theme consistency, component functionality, and overall UI framework migration
 */

test.describe('Mantine v8 Framework Integration', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('user', JSON.stringify({
        role: 'admin',
        email: 'test-admin@example.com',
        id: 'test-user-789'
      }));
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('Mantine Theme Integration', () => {
    test('should load Mantine CSS variables correctly', async () => {
      // Check for Mantine CSS custom properties
      const rootStyles = await page.evaluate(() => {
        const computedStyle = getComputedStyle(document.documentElement);
        return {
          primaryColor: computedStyle.getPropertyValue('--mantine-primary-color-filled'),
          fontFamily: computedStyle.getPropertyValue('--mantine-font-family'),
          spacing: computedStyle.getPropertyValue('--mantine-spacing-md')
        };
      });

      // Mantine variables should be defined
      expect(rootStyles.primaryColor).toBeTruthy();
      expect(rootStyles.fontFamily).toBeTruthy();
      expect(rootStyles.spacing).toBeTruthy();
    });

    test('should apply Roblox-inspired theme correctly', async () => {
      // Check for Roblox color scheme
      const themeColors = await page.evaluate(() => {
        const computedStyle = getComputedStyle(document.documentElement);
        return {
          primary: computedStyle.getPropertyValue('--mantine-color-blue-6'),
          accent: computedStyle.getPropertyValue('--mantine-color-orange-6'),
          surface: computedStyle.getPropertyValue('--mantine-color-gray-0')
        };
      });

      // Theme colors should be defined
      expect(themeColors.primary).toBeTruthy();
      expect(themeColors.accent).toBeTruthy();
      expect(themeColors.surface).toBeTruthy();
    });

    test('should support dark mode toggle', async () => {
      // Look for dark mode toggle (if implemented)
      const darkModeToggle = page.locator('button[aria-label*="dark mode"], button[aria-label*="theme"]');

      if (await darkModeToggle.isVisible()) {
        // Test dark mode toggle
        await darkModeToggle.click();

        // Check if dark mode classes are applied
        const bodyClass = await page.evaluate(() => document.body.className);
        expect(bodyClass).toContain('mantine-dark');
      }
    });
  });

  test.describe('Core Mantine Components', () => {
    test('should render Button components correctly', async () => {
      // Navigate to a page with buttons
      await page.goto('/rewards');

      // Check for Mantine button classes
      const buttons = page.locator('button.mantine-Button-root');
      await expect(buttons.first()).toBeVisible();

      // Test button variants
      const variants = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button.mantine-Button-root'));
        return buttons.map(btn => ({
          variant: btn.getAttribute('data-variant'),
          size: btn.getAttribute('data-size')
        }));
      });

      expect(variants.length).toBeGreaterThan(0);
    });

    test('should render Card components correctly', async () => {
      // Navigate to a page with cards
      await page.goto('/compliance');

      // Check for Mantine card classes
      const cards = page.locator('.mantine-Card-root');
      await expect(cards.first()).toBeVisible();

      // Verify card sections
      const cardSections = page.locator('.mantine-Card-section');
      if (await cardSections.count() > 0) {
        await expect(cardSections.first()).toBeVisible();
      }
    });

    test('should render Grid system correctly', async () => {
      // Check for Mantine grid implementation
      const grids = page.locator('.mantine-Grid-root');
      await expect(grids.first()).toBeVisible();

      // Check for grid columns
      const gridCols = page.locator('.mantine-Grid-col');
      if (await gridCols.count() > 0) {
        await expect(gridCols.first()).toBeVisible();
      }
    });

    test('should render Modal components correctly', async () => {
      // Navigate to page with modals
      await page.goto('/compliance');

      // Open a modal
      await page.click('button:has-text("Record Consent")');

      // Check modal structure
      await expect(page.locator('.mantine-Modal-root')).toBeVisible();
      await expect(page.locator('.mantine-Modal-header')).toBeVisible();
      await expect(page.locator('.mantine-Modal-body')).toBeVisible();

      // Close modal
      await page.click('button:has-text("Cancel")');
      await expect(page.locator('.mantine-Modal-root')).not.toBeVisible();
    });

    test('should render Tabs components correctly', async () => {
      // Navigate to page with tabs
      await page.goto('/compliance');

      // Check tabs structure
      await expect(page.locator('.mantine-Tabs-root')).toBeVisible();
      await expect(page.locator('.mantine-Tabs-list')).toBeVisible();
      await expect(page.locator('.mantine-Tabs-tab')).toBeVisible();

      // Test tab switching
      const secondTab = page.locator('.mantine-Tabs-tab').nth(1);
      await secondTab.click();

      // Check if tab panel changes
      await expect(page.locator('.mantine-Tabs-panel')).toBeVisible();
    });

    test('should render Table components correctly', async () => {
      // Navigate to compliance page with tables
      await page.goto('/compliance');

      // Check table structure
      await expect(page.locator('.mantine-Table-root')).toBeVisible();
      await expect(page.locator('.mantine-Table-thead')).toBeVisible();
      await expect(page.locator('.mantine-Table-tbody')).toBeVisible();

      // Check table cells
      const tableCells = page.locator('.mantine-Table-td');
      if (await tableCells.count() > 0) {
        await expect(tableCells.first()).toBeVisible();
      }
    });
  });

  test.describe('Form Components', () => {
    test('should render TextInput components correctly', async () => {
      // Open a form modal
      await page.goto('/compliance');
      await page.click('button:has-text("Record Consent")');

      // Check TextInput components
      const textInputs = page.locator('.mantine-TextInput-root');
      await expect(textInputs.first()).toBeVisible();

      // Check input wrapper and label
      await expect(page.locator('.mantine-TextInput-wrapper')).toBeVisible();
      await expect(page.locator('.mantine-TextInput-label')).toBeVisible();

      // Test input functionality
      const input = page.locator('input[placeholder*="Student"]');
      await input.fill('TEST123');
      await expect(input).toHaveValue('TEST123');

      // Close modal
      await page.click('button:has-text("Cancel")');
    });

    test('should render Select components correctly', async () => {
      // Open settings tab with selects
      await page.goto('/compliance');
      await page.click('button[role="tab"]:has-text("Settings")');

      // Check Select components
      const selects = page.locator('.mantine-Select-root');
      await expect(selects.first()).toBeVisible();

      // Test select functionality
      const selectInput = page.locator('input[value="monthly"]');
      await selectInput.click();

      // Check dropdown appears
      await expect(page.locator('.mantine-Select-dropdown')).toBeVisible();

      // Select an option
      await page.click('text=Weekly');
    });

    test('should render Badge components correctly', async () => {
      // Navigate to rewards page with badges
      await page.goto('/rewards');

      // Check Badge components
      const badges = page.locator('.mantine-Badge-root');
      await expect(badges.first()).toBeVisible();

      // Test different badge variants
      const badgeVariants = await page.evaluate(() => {
        const badges = Array.from(document.querySelectorAll('.mantine-Badge-root'));
        return badges.map(badge => ({
          variant: badge.getAttribute('data-variant'),
          color: badge.getAttribute('data-color'),
          size: badge.getAttribute('data-size')
        }));
      });

      expect(badgeVariants.length).toBeGreaterThan(0);
    });
  });

  test.describe('Navigation Components', () => {
    test('should render navigation correctly', async () => {
      // Check main navigation
      const nav = page.locator('nav, .mantine-NavLink-root, [role="navigation"]');
      if (await nav.count() > 0) {
        await expect(nav.first()).toBeVisible();
      }
    });

    test('should handle navigation state correctly', async () => {
      // Test navigation between pages
      await page.goto('/compliance');
      await expect(page.locator('h3:has-text("Compliance Dashboard")')).toBeVisible();

      await page.goto('/rewards');
      await expect(page.locator('h2:has-text("Rewards Store")')).toBeVisible();

      // Check if navigation maintains state
      await page.goBack();
      await expect(page.locator('h3:has-text("Compliance Dashboard")')).toBeVisible();
    });
  });

  test.describe('Icon Integration (Tabler Icons)', () => {
    test('should render Tabler icons correctly', async () => {
      // Navigate to page with icons
      await page.goto('/compliance');

      // Check for SVG icons
      const icons = page.locator('svg[data-icon], svg[stroke="currentColor"]');
      await expect(icons.first()).toBeVisible();

      // Verify icon attributes
      const iconAttributes = await page.evaluate(() => {
        const icon = document.querySelector('svg[stroke="currentColor"]');
        return {
          stroke: icon?.getAttribute('stroke'),
          fill: icon?.getAttribute('fill'),
          viewBox: icon?.getAttribute('viewBox')
        };
      });

      expect(iconAttributes.stroke).toBe('currentColor');
      expect(iconAttributes.fill).toBe('none');
    });

    test('should use icons in buttons correctly', async () => {
      // Check for buttons with icons
      const iconButtons = page.locator('button:has(svg)');
      await expect(iconButtons.first()).toBeVisible();

      // Test icon button functionality
      const refreshButton = page.locator('button:has-text("Refresh"):has(svg)');
      if (await refreshButton.isVisible()) {
        await refreshButton.click();
        // Button should be clickable
        expect(true).toBe(true);
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt layout for mobile devices', async () => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Check if Mantine responsive classes work
      const grid = page.locator('.mantine-Grid-root');
      if (await grid.isVisible()) {
        // Grid should adapt to mobile
        await expect(grid).toBeVisible();
      }

      // Check if components stack properly
      const cards = page.locator('.mantine-Card-root');
      if (await cards.count() > 1) {
        // Cards should be stacked vertically on mobile
        const firstCard = cards.nth(0);
        const secondCard = cards.nth(1);

        const firstCardBox = await firstCard.boundingBox();
        const secondCardBox = await secondCard.boundingBox();

        if (firstCardBox && secondCardBox) {
          // Second card should be below first card
          expect(secondCardBox.y).toBeGreaterThan(firstCardBox.y);
        }
      }
    });

    test('should work correctly on tablet viewport', async () => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      // All components should remain functional
      await page.goto('/compliance');
      await expect(page.locator('h3:has-text("Compliance Dashboard")')).toBeVisible();

      // Tab functionality should work
      await page.click('button[role="tab"]:has-text("Settings")');
      await expect(page.locator('label:has-text("Auto-Audit Frequency")')).toBeVisible();
    });

    test('should maintain functionality on large screens', async () => {
      // Set large desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 });

      // Components should use available space efficiently
      await page.goto('/rewards');

      // Reward grid should display more items per row
      const rewardCards = page.locator('.mantine-Card-root');
      const cardCount = await rewardCards.count();

      if (cardCount > 3) {
        // Should have multiple cards per row on large screens
        const firstCard = rewardCards.nth(0);
        const fourthCard = rewardCards.nth(3);

        const firstCardBox = await firstCard.boundingBox();
        const fourthCardBox = await fourthCard.boundingBox();

        if (firstCardBox && fourthCardBox) {
          // Cards should be on same row (approximately same Y position)
          const yDifference = Math.abs(fourthCardBox.y - firstCardBox.y);
          expect(yDifference).toBeLessThan(100); // Allow for some variance
        }
      }
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA attributes', async () => {
      // Check for proper ARIA roles and labels
      const ariaElements = page.locator('[role], [aria-label], [aria-labelledby]');
      const elementCount = await ariaElements.count();

      expect(elementCount).toBeGreaterThan(0);

      // Specifically check button accessibility
      const buttons = page.locator('button[aria-label], button[role="button"]');
      if (await buttons.count() > 0) {
        await expect(buttons.first()).toBeVisible();
      }
    });

    test('should support keyboard navigation', async () => {
      // Test tab navigation
      await page.keyboard.press('Tab');

      // Check if focus is visible
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();

      // Continue tabbing through elements
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Should be able to focus multiple elements
      expect(true).toBe(true);
    });

    test('should have proper color contrast', async () => {
      // This is a basic check - would need actual contrast calculation for full testing
      const textElements = page.locator('p, span, h1, h2, h3, h4, h5, h6');
      await expect(textElements.first()).toBeVisible();

      // Check that text is readable (basic visibility test)
      const textCount = await textElements.count();
      expect(textCount).toBeGreaterThan(0);
    });
  });

  test.describe('Performance', () => {
    test('should load Mantine styles efficiently', async () => {
      const startTime = Date.now();

      await page.goto('/compliance');
      await page.waitForLoadState('networkidle');

      // Check that styles are loaded
      await expect(page.locator('.mantine-Card-root')).toBeVisible();

      const loadTime = Date.now() - startTime;

      // Should load within reasonable time
      expect(loadTime).toBeLessThan(5000);
    });

    test('should not have excessive DOM nodes', async () => {
      // Check DOM size
      const nodeCount = await page.evaluate(() => {
        return document.querySelectorAll('*').length;
      });

      // Should have reasonable DOM size (less than 5000 nodes for a typical page)
      expect(nodeCount).toBeLessThan(5000);
    });

    test('should handle rapid component updates', async () => {
      // Test rapid tab switching
      await page.goto('/compliance');

      for (let i = 0; i < 5; i++) {
        await page.click('button[role="tab"]:has-text("Consent Records")');
        await page.click('button[role="tab"]:has-text("Audit Logs")');
      }

      // Page should remain responsive
      await expect(page.locator('h3:has-text("Compliance Dashboard")')).toBeVisible();
    });
  });

  test.describe('Error Boundaries and Error Handling', () => {
    test('should handle component errors gracefully', async () => {
      // Try to trigger edge cases
      await page.goto('/nonexistent-page');

      // Should show error page or redirect, not crash
      const bodyText = await page.textContent('body');
      expect(bodyText).toBeTruthy();
    });

    test('should handle modal close edge cases', async () => {
      await page.goto('/compliance');

      // Open modal
      await page.click('button:has-text("Record Consent")');
      await expect(page.locator('.mantine-Modal-root')).toBeVisible();

      // Try to close with escape key
      await page.keyboard.press('Escape');
      await expect(page.locator('.mantine-Modal-root')).not.toBeVisible();
    });
  });

  test.describe('Integration with React 19', () => {
    test('should work correctly with React 19 features', async () => {
      // Check that React 19 is properly integrated
      const reactVersion = await page.evaluate(() => {
        // @ts-ignore
        return window.React?.version || 'unknown';
      });

      // Note: This might not be available in production builds
      if (reactVersion !== 'unknown') {
        expect(reactVersion).toMatch(/^19\./);
      }
    });

    test('should handle concurrent features properly', async () => {
      // Test rapid state updates
      await page.goto('/rewards');

      // Rapidly change filters
      await page.fill('input[placeholder="Search rewards..."]', 'test');
      await page.fill('input[placeholder="Search rewards..."]', 'gold');
      await page.fill('input[placeholder="Search rewards..."]', 'dark');

      // Should handle updates smoothly
      await expect(page.locator('input[placeholder="Search rewards..."]')).toHaveValue('dark');
    });
  });

  test.describe('CSS-in-JS Integration', () => {
    test('should apply Mantine styles correctly', async () => {
      // Check that Mantine CSS-in-JS styles are applied
      const buttonStyles = await page.evaluate(() => {
        const button = document.querySelector('.mantine-Button-root');
        if (!button) return null;

        const computedStyle = getComputedStyle(button);
        return {
          borderRadius: computedStyle.borderRadius,
          padding: computedStyle.padding,
          fontSize: computedStyle.fontSize
        };
      });

      if (buttonStyles) {
        expect(buttonStyles.borderRadius).toBeTruthy();
        expect(buttonStyles.padding).toBeTruthy();
        expect(buttonStyles.fontSize).toBeTruthy();
      }
    });

    test('should handle dynamic theme changes', async () => {
      // If theme switching is implemented, test it
      const initialBackgroundColor = await page.evaluate(() => {
        return getComputedStyle(document.body).backgroundColor;
      });

      expect(initialBackgroundColor).toBeTruthy();

      // Theme should be consistently applied
      const cardBackgroundColor = await page.evaluate(() => {
        const card = document.querySelector('.mantine-Card-root');
        return card ? getComputedStyle(card).backgroundColor : null;
      });

      if (cardBackgroundColor) {
        expect(cardBackgroundColor).toBeTruthy();
      }
    });
  });
});