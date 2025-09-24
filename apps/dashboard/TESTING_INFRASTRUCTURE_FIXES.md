# Testing Infrastructure Fixes - Implementation Plan

## Current Status Analysis

### Issues Identified
1. **React Hooks Error**: Store type mismatch between test store and actual store
2. **Complex Store Dependencies**: RTK Query, WebSocket middleware, Pusher service
3. **Import Path Conflicts**: Multiple render utilities causing confusion
4. **Clerk Authentication**: No proper mocking strategy in place

### Root Cause
The Login component uses `useAppDispatch()` which expects a complex store with RTK Query and WebSocket middleware, but our test store is simplified.

## Immediate Fixes (Ready to Implement)

### 1. Fix Store Type Compatibility (PRIORITY 1)

**Problem**: Test store doesn't match the real store structure
**Solution**: Create test store that mirrors the real store but with mocks

```typescript
// src/test/utils/test-store.ts
import { configureStore } from '@reduxjs/toolkit';
import { api } from '@/store/api';
import userReducer from '@/store/slices/userSlice';
import uiReducer from '@/store/slices/uiSlice';
// ... other reducers

export const createTestStore = (preloadedState = {}) => {
  return configureStore({
    reducer: {
      [api.reducerPath]: api.reducer,
      user: userReducer,
      ui: uiReducer,
      // ... other reducers
    },
    preloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }).concat(api.middleware),
  });
};
```

### 2. Mock WebSocket and Pusher Services (PRIORITY 1)

**Problem**: Store initialization tries to create real WebSocket/Pusher connections
**Solution**: Mock these services globally in test setup

```typescript
// Already implemented in src/test/setup.ts - expand it
vi.mock('@/services/pusher', () => ({
  PusherService: {
    getInstance: vi.fn(() => ({
      connect: vi.fn(),
      disconnect: vi.fn(),
      subscribe: vi.fn(() => ({ bind: vi.fn(), unbind: vi.fn() })),
      // ... other methods
    }))
  }
}));
```

### 3. Simplify Test Approach (QUICK WIN)

**Current approach**: Complex provider setup causing hooks issues
**Better approach**: Use real store with mocked dependencies

### 4. Clerk Authentication Strategy (PRIORITY 2)

**Recommendation**: Mock Clerk entirely for tests (already implemented in setup.ts)
**Rationale**:
- External service - don't test Clerk's implementation
- Need deterministic auth states for testing
- Faster test execution
- No external dependencies

## Implementation Steps

### Step 1: Fix Store Compatibility (30 minutes)

1. **Update test store to match real store**:
   ```bash
   # Create proper test store
   touch src/test/utils/enhanced-test-store.ts
   ```

2. **Update Login test to use compatible store**:
   ```typescript
   // Use real reducers with mocked services
   import { createTestStore } from '@/test/utils/enhanced-test-store';
   ```

### Step 2: Enhanced Mock Strategy (20 minutes)

1. **Mock RTK Query in tests**:
   ```typescript
   // Mock API calls to return successful responses
   vi.mock('@/store/api', () => ({
     api: {
       reducer: (state = {}, action) => state,
       middleware: (store) => (next) => (action) => next(action),
       reducerPath: 'api'
     }
   }));
   ```

2. **Mock WebSocket middleware**:
   ```typescript
   vi.mock('@/store/middleware/websocketMiddleware', () => ({
     createWebSocketMiddleware: vi.fn(() => (store) => (next) => (action) => next(action)),
     setupWebSocketListeners: vi.fn()
   }));
   ```

### Step 3: Test Verification (10 minutes)

1. **Run Login test**:
   ```bash
   npm run test -- src/__tests__/components/pages/Login.test.tsx
   ```

2. **Expected result**: Test should pass without React hooks errors

## Long-term Strategy (Next Steps)

### 1. Component Test Templates

Create standardized test templates for each component type:

```typescript
// src/test/templates/page-component.test.template.ts
describe('PageComponent', () => {
  describe('Rendering', () => {
    it('should render with required props');
    it('should handle loading states');
    it('should handle error states');
  });

  describe('User Interactions', () => {
    it('should handle form submissions');
    it('should handle navigation');
  });

  describe('Authentication States', () => {
    it('should render for authenticated users');
    it('should render for unauthenticated users');
    it('should handle role-based access');
  });
});
```

### 2. Test Utilities Library

```typescript
// src/test/utils/index.ts
export { render, renderWithAuth, renderUnauthenticated } from './render';
export { createTestStore, createMockUser, createMockClass } from './test-helpers';
export { mockApiResponse, waitForLoadingToFinish } from './api-helpers';
export { ClerkMockProvider, useClerkMockControls } from './clerk-mock-provider';
```

### 3. Coverage Automation

```bash
# Add to package.json scripts
"test:coverage:watch": "vitest run --coverage --watch",
"test:coverage:report": "vitest run --coverage && open coverage/index.html",
"test:component": "vitest run src/**/*.test.tsx",
"test:hooks": "vitest run src/hooks/**/*.test.ts",
"test:services": "vitest run src/services/**/*.test.ts"
```

## E2E Testing Strategy

### Mock vs Real Authentication

**Recommendation**: Use mock authentication for E2E tests by default

**Implementation**:
```typescript
// e2e/utils/auth-helper.ts (already created)
// Environment variable controls mock vs real:
// E2E_AUTH_MODE=mock (default) or E2E_AUTH_MODE=real

// Usage in tests:
await authenticate(page, 'admin'); // Uses mock by default
await authenticate(page, 'teacher', 'real'); // Uses real Clerk
```

### E2E Test Categories

1. **Smoke Tests**: Basic page loads and navigation
2. **User Flows**: Complete user journeys (login → dashboard → action)
3. **Cross-browser**: Key flows in Chrome, Firefox, Safari
4. **Performance**: Page load times, interaction responsiveness

## Success Metrics

### Phase 1 (Infrastructure Fix) - Target: 2 days
- [ ] Login test passes without React hooks errors
- [ ] Basic component tests can be written easily
- [ ] Test store matches real store capabilities

### Phase 2 (Coverage Boost) - Target: 1 week
- [ ] 50+ component tests passing
- [ ] All service functions tested
- [ ] 70%+ line coverage achieved

### Phase 3 (Full Coverage) - Target: 2 weeks
- [ ] 90%+ line coverage
- [ ] All critical user flows tested in E2E
- [ ] Test suite runs in <5 minutes

## Risk Mitigation

1. **Test Flakiness**: Use deterministic mocks, avoid timeouts
2. **Maintenance Burden**: Create test templates and generators
3. **Performance**: Run tests in parallel, optimize test setup
4. **Coverage Gaps**: Automated coverage reporting and CI checks

## Next Actions

1. **Implement Step 1** (Fix store compatibility)
2. **Verify Login test passes**
3. **Create 5 more component tests using same pattern**
4. **Run coverage report to identify next priorities**

This approach will give us a solid foundation for rapidly scaling test coverage while maintaining reliability and maintainability.