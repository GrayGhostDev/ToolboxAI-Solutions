# E2E Testing Selector Strategy Guide

## Material-UI Component Selectors

### Key Insights from Testing

1. **Strict Mode Issues**: When multiple elements match, use `.first()`, `.nth()`, or more specific selectors
2. **MUI Overlays**: Dropdowns create backdrop overlays that can block interactions
3. **Dynamic Content**: Components may take time to render, always use proper wait conditions

### Recommended Selector Patterns

#### Text-based Selectors
```typescript
// ✅ Good - Use first() for multiple matches
await expect(page.getByText('Total Students').first()).toBeVisible();

// ✅ Good - Use exact match for navigation
const classesLink = page.getByText('Classes', { exact: true });

// ❌ Bad - Will fail in strict mode if multiple elements match
await expect(page.getByText('Total Students')).toBeVisible();
```

#### MUI Select/Dropdown Interactions
```typescript
// ✅ Good - Click the combobox element directly
const gradeSelect = page.locator('div[role="combobox"]').first();
await gradeSelect.click();
await page.waitForTimeout(300);
await page.getByRole('option', { name: '5th Grade' }).click();
// Close dropdown to prevent overlay issues
await page.keyboard.press('Escape');

// ❌ Bad - Clicking labels can be intercepted
await page.locator('label:has-text("Grade Level")').click();
```

#### Form Input Fields
```typescript
// ✅ Good - Multiple fallback strategies
const classNameInput = page.locator('input[placeholder*="Math 101"]');
if (!(await classNameInput.isVisible())) {
  const classNameField = page.locator('label:has-text("Class Name")')
    .locator('..')
    .locator('input');
  await classNameField.fill('Test Class');
} else {
  await classNameInput.fill('Test Class');
}
```

#### Button Interactions
```typescript
// ✅ Good - Use role with name for specificity
const createButton = page.getByRole('button', { name: /Create Class/i });
await expect(createButton).toBeVisible({ timeout: 10000 });
await createButton.click();

// ✅ Good - Filter by text for multiple buttons
const createButton = page.getByRole('button').filter({ hasText: 'Create Class' });
```

#### Navigation Helpers
```typescript
// ✅ Good - Check sidebar visibility before clicking
async function navigateToClasses(page: Page) {
  const classesLink = page.getByText('Classes', { exact: true });

  if (!(await classesLink.isVisible())) {
    const menuButton = page.locator('button[aria-label*="menu"]');
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(500);
    }
  }

  await classesLink.click();
  await page.waitForURL(/\/classes/, { timeout: 10000 });
  await page.waitForLoadState('networkidle');
}
```

### Wait Strategies

#### For Page Load
```typescript
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000); // Additional buffer for dynamic content
```

#### For Dialog/Modal
```typescript
await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 });
```

#### For Dynamic Content
```typescript
// Wait for specific element with timeout
await expect(element).toBeVisible({ timeout: 10000 });

// Wait for URL change
await page.waitForURL(/\/classes/, { timeout: 10000 });
```

### Common MUI Components

#### Cards
```typescript
const classCard = page.locator('.MuiCard-root').filter({
  hasText: /Mathematics 101/
});
```

#### Data Grids
```typescript
const dataGrid = page.locator('.MuiDataGrid-root').first();
```

#### Dialogs
```typescript
const dialog = page.getByRole('dialog');
await expect(dialog).toBeVisible();
```

### Error Prevention

1. **Always use timeouts**: Default timeouts may be too short for complex components
2. **Close dropdowns**: Use ESC key after selecting to prevent overlay issues
3. **Check visibility**: Verify elements are visible before interaction
4. **Use networkidle**: Wait for all network requests to complete
5. **Handle optional fields**: Wrap optional interactions in try-catch

### Debugging Tips

1. Use `--headed` flag to see what's happening
2. Take screenshots on failure: `await page.screenshot({ path: 'debug.png' })`
3. Use `page.pause()` for interactive debugging
4. Check error context files in `test-results/` directory

### Test Structure Best Practices

```typescript
test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: login, navigation
  });

  test('should do something', async ({ page }) => {
    // Arrange: setup test data
    // Act: perform actions
    // Assert: verify results
  });
});
```

### Role-based Testing

```typescript
// Helper for role-based login with Clerk authentication
async function loginAs(page: Page, role: 'teacher' | 'student' | 'admin') {
  const credentials = {
    teacher: { email: 'jane.smith@school.edu', password: 'Teacher123!' },
    student: { email: 'alex.johnson@student.edu', password: 'Student123!' },
    admin: { email: 'admin@toolboxai.com', password: 'Admin123!' }
  };

  await page.goto('/login');
  // Use Clerk-specific selectors - Clerk uses "identifier" instead of "email"
  await page.locator('input[name="identifier"], input[id="identifier-field"]').fill(credentials[role].email);
  await page.locator('input[name="password"], input[id="password-field"]').fill(credentials[role].password);
  await page.locator('button[type="submit"], button:has-text("Continue")').click();
  await page.waitForURL(url => !url.pathname.includes('/login'));
}
```

## Summary

The key to successful E2E testing with Material-UI components is:
1. Understanding how MUI renders components (overlays, animations)
2. Using appropriate wait strategies
3. Having fallback selectors for dynamic content
4. Properly handling strict mode with specific element selection
5. Cleaning up after interactions (closing dropdowns, dialogs)