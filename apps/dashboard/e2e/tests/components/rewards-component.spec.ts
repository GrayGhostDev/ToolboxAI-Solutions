import { test, expect, Page } from '@playwright/test';

/**
 * Comprehensive Playwright tests for the Rewards component (Mantine migration)
 * Tests component rendering, tab navigation, modal interactions, cart functionality, and filtering
 */

test.describe('Rewards Component - Mantine Migration', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Mock authentication and gamification data
    await page.addInitScript(() => {
      localStorage.setItem('user', JSON.stringify({
        role: 'teacher',
        email: 'test-teacher@example.com',
        id: 'test-user-456'
      }));

      // Mock Redux state for gamification
      window.__REDUX_STORE__ = {
        getState: () => ({
          gamification: {
            xp: 1500,
            level: 15,
            badges: ['gold_star', 'perfect_score', 'consistent_learner']
          },
          user: {
            role: 'teacher'
          }
        })
      };
    });

    // Navigate to rewards page
    await page.goto('/rewards');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('Component Rendering', () => {
    test('should render rewards store header correctly', async () => {
      // Check main header
      await expect(page.locator('h2:has-text("Rewards Store")')).toBeVisible();

      // Check XP badge
      await expect(page.locator('.mantine-Badge-root:has-text("XP Available")')).toBeVisible();

      // Check level badge
      await expect(page.locator('.mantine-Badge-root:has-text("Level")')).toBeVisible();

      // Check badges count
      await expect(page.locator('.mantine-Badge-root:has-text("Badges")')).toBeVisible();
    });

    test('should display teacher-specific controls', async () => {
      // Create Reward button (teacher only)
      await expect(page.locator('button:has-text("Create Reward")')).toBeVisible();

      // Cart button
      await expect(page.locator('button:has-text("Cart")')).toBeVisible();

      // Manage tab should be visible for teachers
      await expect(page.locator('button[role="tab"]:has-text("Manage")')).toBeVisible();
    });

    test('should render all tab options', async () => {
      // Check tab list
      await expect(page.locator('.mantine-Tabs-list')).toBeVisible();

      // Check all tabs
      await expect(page.locator('button[role="tab"]:has-text("Available Rewards")')).toBeVisible();
      await expect(page.locator('button[role="tab"]:has-text("My Rewards")')).toBeVisible();
      await expect(page.locator('button[role="tab"]:has-text("History")')).toBeVisible();
      await expect(page.locator('button[role="tab"]:has-text("Manage")')).toBeVisible();
    });

    test('should display filter controls', async () => {
      // Search input
      await expect(page.locator('input[placeholder="Search rewards..."]')).toBeVisible();

      // Category selector
      await expect(page.locator('input[placeholder="Category"]')).toBeVisible();

      // Test search functionality
      await page.fill('input[placeholder="Search rewards..."]', 'Golden');
      await expect(page.locator('input[placeholder="Search rewards..."]')).toHaveValue('Golden');
    });
  });

  test.describe('Available Rewards Tab', () => {
    test('should display reward cards with proper information', async () => {
      // Ensure we're on Available Rewards tab
      await page.click('button[role="tab"]:has-text("Available Rewards")');

      // Check for reward cards
      const rewardCards = page.locator('.mantine-Card-root').filter({ hasText: 'XP' });
      await expect(rewardCards.first()).toBeVisible();

      // Check for reward names
      await expect(page.locator('text=Golden Avatar Frame')).toBeVisible();
      await expect(page.locator('text=Dark Mode Theme')).toBeVisible();
      await expect(page.locator('text=Double XP Booster')).toBeVisible();

      // Check for rarity badges
      await expect(page.locator('.mantine-Badge-root:has-text("EPIC")')).toBeVisible();
      await expect(page.locator('.mantine-Badge-root:has-text("RARE")')).toBeVisible();
      await expect(page.locator('.mantine-Badge-root:has-text("LEGENDARY")')).toBeVisible();
    });

    test('should show requirement badges for locked rewards', async () => {
      // Look for level requirement badges
      await expect(page.locator('.mantine-Badge-root:has-text("Level")')).toBeVisible();

      // Check for lock icons on unavailable rewards
      const lockIcons = page.locator('[data-icon="lock"]');
      if (await lockIcons.count() > 0) {
        await expect(lockIcons.first()).toBeVisible();
      }
    });

    test('should handle reward interactions', async () => {
      // Find a redeemable reward
      const redeemButton = page.locator('button:has-text("Redeem")').first();

      if (await redeemButton.isEnabled()) {
        await redeemButton.click();

        // Should open confirmation modal
        await expect(page.locator('.mantine-Modal-root')).toBeVisible();
        await expect(page.locator('text=Confirm Redemption')).toBeVisible();

        // Close modal
        await page.click('button:has-text("Cancel")');
        await expect(page.locator('.mantine-Modal-root')).not.toBeVisible();
      }
    });

    test('should handle add to cart functionality', async () => {
      // Find add to cart button (plus icon)
      const addToCartButton = page.locator('button[aria-label="Add to cart"]').first();

      if (await addToCartButton.isVisible() && await addToCartButton.isEnabled()) {
        await addToCartButton.click();

        // Cart button should update to show items
        await expect(page.locator('button:has-text("Cart")')).toBeVisible();
      }
    });
  });

  test.describe('Filter and Search Functionality', () => {
    test('should filter rewards by category', async () => {
      // Click category selector
      await page.click('input[placeholder="Category"]');

      // Select avatar category
      await page.click('text=Avatars');

      // Should show only avatar rewards
      await expect(page.locator('text=Golden Avatar Frame')).toBeVisible();

      // Reset filter
      await page.click('input[placeholder="Category"]');
      await page.click('text=All Categories');
    });

    test('should search rewards by name', async () => {
      // Search for specific reward
      await page.fill('input[placeholder="Search rewards..."]', 'Dark Mode');

      // Should show only matching rewards
      await expect(page.locator('text=Dark Mode Theme')).toBeVisible();

      // Clear search
      await page.fill('input[placeholder="Search rewards..."]', '');
    });

    test('should combine search and filter', async () => {
      // Set category filter
      await page.click('input[placeholder="Category"]');
      await page.click('text=Power-ups');

      // Add search term
      await page.fill('input[placeholder="Search rewards..."]', 'Double');

      // Should show only matching power-ups
      await expect(page.locator('text=Double XP Booster')).toBeVisible();
    });
  });

  test.describe('Tab Navigation', () => {
    test('should navigate between tabs correctly', async () => {
      // Start on Available Rewards (default)
      await expect(page.locator('button[role="tab"][data-active="true"]:has-text("Available Rewards")')).toBeVisible();

      // Navigate to My Rewards
      await page.click('button[role="tab"]:has-text("My Rewards")');
      await expect(page.locator('text=Your Redeemed Rewards')).toBeVisible();

      // Navigate to History
      await page.click('button[role="tab"]:has-text("History")');
      await expect(page.locator('text=Redeemed on')).toBeVisible();

      // Navigate to Manage (teacher only)
      await page.click('button[role="tab"]:has-text("Manage")');
      await expect(page.locator('text=Manage Rewards')).toBeVisible();
    });

    test('should maintain state across tab switches', async () => {
      // Set search filter
      await page.fill('input[placeholder="Search rewards..."]', 'Golden');

      // Switch tabs
      await page.click('button[role="tab"]:has-text("History")');
      await page.click('button[role="tab"]:has-text("Available Rewards")');

      // Search should still be applied
      await expect(page.locator('input[placeholder="Search rewards..."]')).toHaveValue('Golden');
    });
  });

  test.describe('My Rewards Tab', () => {
    test('should display redeemed rewards', async () => {
      // Navigate to My Rewards tab
      await page.click('button[role="tab"]:has-text("My Rewards")');

      // Check information alert
      await expect(page.locator('text=Your Redeemed Rewards')).toBeVisible();
      await expect(page.locator('text=These are the rewards you\'ve already redeemed')).toBeVisible();

      // Check for reward cards (if any exist)
      const rewardCards = page.locator('.mantine-Card-root');
      if (await rewardCards.count() > 0) {
        await expect(rewardCards.first()).toBeVisible();
      }
    });

    test('should show activate button for power-ups', async () => {
      // Navigate to My Rewards tab
      await page.click('button[role="tab"]:has-text("My Rewards")');

      // Look for power-up rewards with activate buttons
      const activateButton = page.locator('button:has-text("Activate")');
      if (await activateButton.count() > 0) {
        await expect(activateButton.first()).toBeVisible();
      }
    });
  });

  test.describe('History Tab', () => {
    test('should display reward history', async () => {
      // Navigate to History tab
      await page.click('button[role="tab"]:has-text("History")');

      // Check for history items
      const historyItems = page.locator('.mantine-Paper-root').filter({ hasText: 'Redeemed on' });
      if (await historyItems.count() > 0) {
        await expect(historyItems.first()).toBeVisible();

        // Check for status badges
        await expect(page.locator('.mantine-Badge-root').first()).toBeVisible();
      }
    });

    test('should display reward details in history', async () => {
      // Navigate to History tab
      await page.click('button[role="tab"]:has-text("History")');

      // Look for specific history items
      const historyText = page.locator('text=Double XP Booster');
      if (await historyText.isVisible()) {
        await expect(historyText).toBeVisible();
      }
    });
  });

  test.describe('Manage Tab (Teacher Only)', () => {
    test('should display manage interface for teachers', async () => {
      // Navigate to Manage tab
      await page.click('button[role="tab"]:has-text("Manage")');

      // Check manage information
      await expect(page.locator('text=Manage Rewards')).toBeVisible();
      await expect(page.locator('text=Create custom rewards for your students')).toBeVisible();

      // Check Create New Reward button
      await expect(page.locator('button:has-text("Create New Reward")')).toBeVisible();

      // Check Active Rewards section
      await expect(page.locator('h3:has-text("Active Rewards")')).toBeVisible();
    });

    test('should display existing rewards for management', async () => {
      // Navigate to Manage tab
      await page.click('button[role="tab"]:has-text("Manage")');

      // Check for reward management items
      const managementItems = page.locator('.mantine-Paper-root').filter({ hasText: 'Edit' });
      if (await managementItems.count() > 0) {
        await expect(managementItems.first()).toBeVisible();

        // Check for Edit and Remove buttons
        await expect(page.locator('button:has-text("Edit")')).toBeVisible();
        await expect(page.locator('button:has-text("Remove")')).toBeVisible();
      }
    });
  });

  test.describe('Modal Interactions', () => {
    test('should open and close redemption confirmation modal', async () => {
      // Find and click redeem button
      const redeemButton = page.locator('button:has-text("Redeem")').first();

      if (await redeemButton.isEnabled()) {
        await redeemButton.click();

        // Modal should be visible
        await expect(page.locator('.mantine-Modal-root')).toBeVisible();
        await expect(page.locator('text=Confirm Redemption')).toBeVisible();

        // Check modal content
        await expect(page.locator('text=Are you sure you want to redeem')).toBeVisible();
        await expect(page.locator('text=This will cost')).toBeVisible();

        // Test cancel
        await page.click('button:has-text("Cancel")');
        await expect(page.locator('.mantine-Modal-root')).not.toBeVisible();
      }
    });

    test('should open and close create reward modal', async () => {
      // Click Create Reward button
      await page.click('button:has-text("Create Reward")');

      // Modal should be visible
      await expect(page.locator('.mantine-Modal-root')).toBeVisible();
      await expect(page.locator('text=Create New Reward')).toBeVisible();

      // Check form fields
      await expect(page.locator('input[placeholder="Enter reward name"]')).toBeVisible();
      await expect(page.locator('input[placeholder="Enter reward description"]')).toBeVisible();
      await expect(page.locator('input[placeholder="Select category"]')).toBeVisible();

      // Close modal
      await page.click('button:has-text("Cancel")');
      await expect(page.locator('.mantine-Modal-root')).not.toBeVisible();
    });

    test('should validate create reward form', async () => {
      // Open create reward modal
      await page.click('button:has-text("Create Reward")');

      // Fill out form
      await page.fill('input[placeholder="Enter reward name"]', 'Test Reward');
      await page.fill('input[placeholder="Enter reward description"]', 'A test reward for validation');

      // Select category
      await page.click('input[placeholder="Select category"]');
      await page.click('text=Avatar');

      // Fill XP cost
      await page.fill('input[placeholder="Enter XP cost"]', '250');

      // Select rarity
      await page.click('input[placeholder="Select rarity"]');
      await page.click('text=Rare');

      // Submit form
      await page.click('button:has-text("Create Reward")');

      // Modal should close
      await expect(page.locator('.mantine-Modal-root')).not.toBeVisible();
    });
  });

  test.describe('Cart Functionality', () => {
    test('should handle empty cart state', async () => {
      // Cart button should be disabled when empty
      const cartButton = page.locator('button:has-text("Cart")');
      await expect(cartButton).toBeDisabled();
    });

    test('should add items to cart and update button', async () => {
      // Find and click add to cart button
      const addButton = page.locator('button[aria-label="Add to cart"]').first();

      if (await addButton.isVisible() && await addButton.isEnabled()) {
        await addButton.click();

        // Cart button should now be enabled and show count
        const cartButton = page.locator('button:has-text("Cart")');
        await expect(cartButton).toBeEnabled();
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt to mobile viewport', async () => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      // Header should be responsive
      await expect(page.locator('h2:has-text("Rewards Store")')).toBeVisible();

      // Reward grid should adapt
      await expect(page.locator('.mantine-SimpleGrid-root')).toBeVisible();

      // Tabs should remain functional
      await page.click('button[role="tab"]:has-text("History")');
      await expect(page.locator('text=Redeemed on')).toBeVisible();
    });

    test('should work on tablet viewport', async () => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      // All components should remain functional
      await expect(page.locator('h2:has-text("Rewards Store")')).toBeVisible();
      await expect(page.locator('.mantine-Tabs-root')).toBeVisible();

      // Cards should display properly
      const rewardCards = page.locator('.mantine-Card-root');
      await expect(rewardCards.first()).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle insufficient XP gracefully', async () => {
      // Mock low XP state
      await page.evaluate(() => {
        window.__REDUX_STORE__ = {
          getState: () => ({
            gamification: {
              xp: 50, // Low XP
              level: 1,
              badges: []
            },
            user: {
              role: 'student'
            }
          })
        };
      });

      await page.reload();

      // Expensive rewards should be disabled
      const expensiveRewards = page.locator('button:has-text("Redeem")[disabled]');
      if (await expensiveRewards.count() > 0) {
        await expect(expensiveRewards.first()).toBeDisabled();
      }
    });

    test('should handle low level restrictions', async () => {
      // Mock low level state
      await page.evaluate(() => {
        window.__REDUX_STORE__ = {
          getState: () => ({
            gamification: {
              xp: 2000,
              level: 5, // Low level
              badges: []
            },
            user: {
              role: 'student'
            }
          })
        };
      });

      await page.reload();

      // High-level rewards should show lock icons
      const lockIcons = page.locator('[data-icon="lock"]');
      if (await lockIcons.count() > 0) {
        await expect(lockIcons.first()).toBeVisible();
      }
    });
  });

  test.describe('Performance', () => {
    test('should load reward cards efficiently', async () => {
      const startTime = Date.now();

      await page.goto('/rewards');
      await page.waitForLoadState('networkidle');

      // Wait for reward cards to be visible
      await expect(page.locator('.mantine-Card-root').first()).toBeVisible();

      const loadTime = Date.now() - startTime;

      // Should load within reasonable time
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle large numbers of rewards', async () => {
      // This test would be more meaningful with a larger dataset
      // For now, verify that the grid layout handles multiple items
      const rewardCards = page.locator('.mantine-Card-root');
      const cardCount = await rewardCards.count();

      // Should have multiple reward cards
      expect(cardCount).toBeGreaterThan(0);
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels and roles', async () => {
      // Check tab accessibility
      await expect(page.locator('button[role="tab"]').first()).toHaveAttribute('role', 'tab');

      // Check button accessibility
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();
      expect(buttonCount).toBeGreaterThan(0);

      // Modal should have proper accessibility
      await page.click('button:has-text("Create Reward")');
      await expect(page.locator('[role="dialog"]')).toBeVisible();
      await page.click('button:has-text("Cancel")');
    });

    test('should support keyboard navigation', async () => {
      // Focus on first tab
      await page.locator('button[role="tab"]').first().focus();

      // Should be able to navigate with arrow keys
      await page.keyboard.press('ArrowRight');

      // Check if focus moved to next tab
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toHaveAttribute('role', 'tab');
    });
  });
});