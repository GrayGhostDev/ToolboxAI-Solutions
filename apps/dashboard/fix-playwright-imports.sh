#!/bin/bash

# Fix all Playwright import issues

echo "Fixing Playwright imports..."

# Fix Page imports in test files
sed -i '' 's/import { test, expect, Page }/import { test, expect } from '"'"'@playwright\/test'"'"';\nimport type { Page }/' e2e/tests/features/messages.spec.ts
sed -i '' 's/import { test, expect, Page }/import { test, expect } from '"'"'@playwright\/test'"'"';\nimport type { Page }/' e2e/tests/features/classes.spec.ts
sed -i '' 's/import { test, expect, Page }/import { test, expect } from '"'"'@playwright\/test'"'"';\nimport type { Page }/' e2e/tests/features/lessons.spec.ts
sed -i '' 's/import { test, expect, Page }/import { test, expect } from '"'"'@playwright\/test'"'"';\nimport type { Page }/' e2e/tests/simple-test.spec.ts
sed -i '' 's/import { test as base, Page }/import { test as base } from '"'"'@playwright\/test'"'"';\nimport type { Page }/' e2e/fixtures/auth.fixture.ts

# Fix expect and Locator imports in page objects
sed -i '' 's/import type { Page, expect, Locator }/import type { Page, Locator } from '"'"'@playwright\/test'"'"';\nimport { expect }/' e2e/pages/DashboardPage.ts
sed -i '' 's/import type { Page, expect }/import type { Page } from '"'"'@playwright\/test'"'"';\nimport { expect }/' e2e/pages/LoginPage.ts
sed -i '' 's/import type { Page, expect }/import type { Page } from '"'"'@playwright\/test'"'"';\nimport { expect }/' e2e/pages/AdminDashboardPage.ts

# Fix any other Page imports
find e2e -name "*.ts" -type f -exec sed -i '' 's/import { Page }/import type { Page }/' {} \;

echo "Done fixing imports!"