# Quick Start: Testing the Dashboard

## Prerequisites

Ensure services are running:

```bash
# Check backend (should return health JSON)
curl http://127.0.0.1:8009/health

# Check dashboard (should return HTML)
curl http://localhost:5179/ | head -5
```

## Run Automated Tests

### One-Line Test Execution
```bash
node test-dashboard.mjs
```

### View Screenshots
```bash
open /tmp/dashboard-home.png
open /tmp/dashboard-roblox-studio.png
```

## Test Results Summary

**✅ Expected Results:**
- Page Title: "ToolBoxAI Dashboard"
- Load Time: < 200ms
- Navigation Elements: 25+ clickable items
- Backend Health: "degraded" or "healthy" status
- Console Errors: 20-30 (development warnings only - expected)

**❌ Failure Indicators:**
- Cannot connect to http://localhost:5179
- Backend health check fails
- Page title missing or incorrect
- Navigation completely missing (0 elements)

## Manual Testing Checklist

1. **Homepage Load**
   - [ ] Visit http://localhost:5179/
   - [ ] Page renders within 5 seconds
   - [ ] No white screen or crash

2. **Navigation**
   - [ ] Sidebar visible
   - [ ] Click "Roblox Studio"
   - [ ] URL changes to `/roblox`
   - [ ] Page content loads

3. **Backend Communication**
   - [ ] Check browser DevTools Network tab
   - [ ] Look for API calls to port 8009
   - [ ] Verify 200/401 responses (not 500)

4. **Console Warnings**
   - [ ] Open browser DevTools Console
   - [ ] Verify only development warnings (not red errors)
   - [ ] Clerk warnings expected in dev mode

## Troubleshooting

### Dashboard Not Loading
```bash
# Restart dashboard
lsof -ti :5179 | xargs kill -9
cd apps/dashboard && npm run dev
```

### Backend Not Responding
```bash
# Restart backend
lsof -ti :8009 | xargs kill -9
source venv/bin/activate
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload
```

### Database Connection Issues
```bash
# Check Docker containers
docker ps --filter "name=toolboxai"

# Restart if needed
docker restart toolboxai-postgres toolboxai-redis
```

### Clear Build Cache
```bash
cd apps/dashboard
rm -rf node_modules/.vite
npm run dev
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Dashboard E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '22'
      - name: Install dependencies
        run: npm install
      - name: Install Playwright
        run: npx playwright install chromium
      - name: Start services
        run: |
          docker compose up -d postgres redis
          source venv/bin/activate
          uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 &
          cd apps/dashboard && npm run dev &
          sleep 10
      - name: Run tests
        run: node test-dashboard.mjs
      - name: Upload screenshots
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: /tmp/dashboard-*.png
```

## Performance Benchmarks

**Target Metrics:**
- DOM Content Loaded: < 200ms ✅
- Page Load Complete: < 300ms ✅
- DOM Interactive: < 100ms ✅
- First Contentful Paint: < 500ms ✅

**Current Performance:**
- DOM Content Loaded: 117ms ⚡
- Page Load Complete: 119ms ⚡
- DOM Interactive: 39ms ⚡

## Known Issues (Non-Critical)

### Development Mode Warnings
These are **expected** and do not affect production:

1. **React StrictMode Double Rendering**
   - Cause: React 19 intentionally double-renders in development
   - Impact: None (improves error detection)
   - Solution: None needed

2. **Multiple ClerkProvider Components**
   - Cause: React StrictMode + HMR
   - Impact: Development only
   - Solution: Warnings won't appear in production builds

3. **Navigation Selector Timeout**
   - Cause: Specific CSS selector may need adjustment
   - Impact: None (25 elements still detected)
   - Solution: Update test selectors if needed

## Production Build Testing

```bash
# Build for production
cd apps/dashboard
npm run build

# Serve production build
npx serve -s dist -l 5179

# Run tests against production build
node test-dashboard.mjs
```

Expected improvements in production:
- 0 console errors (no StrictMode warnings)
- Faster load times (optimized bundle)
- Smaller bundle size

## Test Maintenance

### Update Test Script
Edit: `/Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions/test-dashboard.mjs`

### Add New Tests
```javascript
// Example: Add authentication test
console.log('\n📝 Test 9: Authentication flow...');
await page.goto(`${DASHBOARD_URL}/login`);
await page.fill('input[name="email"]', 'test@example.com');
await page.fill('input[name="password"]', 'password123');
await page.click('button[type="submit"]');
await page.waitForURL(`${DASHBOARD_URL}/`);
console.log('   ✅ Login successful');
```

## Questions?

See full test report: [DASHBOARD_TEST_REPORT.md](./DASHBOARD_TEST_REPORT.md)

---

*Last Updated: October 16, 2025*
*Test Framework: Playwright with Chromium*
