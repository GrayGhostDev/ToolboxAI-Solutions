# Dual-Mode Authentication System

## Overview

The authentication system now supports dual-mode operation, allowing seamless switching between:
- **Production Mode**: Uses real fetch, localStorage, and BroadcastChannel APIs
- **Mock Mode**: Uses mock implementations for testing and development
- **Test Mode**: Automatically uses mocks when running tests

## Environment Variables

Configure the auth system behavior using these environment variables:

```bash
# .env.local (for development)
VITE_AUTH_MODE=development        # development | test | production
VITE_USE_MOCK_AUTH=false         # true to use mock auth in development
VITE_ENABLE_AUTO_REFRESH=true    # Enable automatic token refresh
VITE_ENABLE_SESSION_MONITORING=true  # Enable session monitoring
VITE_ENABLE_CROSS_TAB_SYNC=true  # Enable cross-tab synchronization
VITE_ENABLE_RETRY_LOGIC=true     # Enable retry logic for API calls
VITE_ENABLE_ERROR_RECOVERY=true  # Enable error recovery mechanisms

# Timing configurations (in minutes)
VITE_TOKEN_REFRESH_THRESHOLD=5   # Refresh token X minutes before expiry
VITE_SESSION_TIMEOUT=30          # Session timeout after X minutes
VITE_INACTIVITY_WARNING=25       # Show warning after X minutes
VITE_MAX_RETRY_ATTEMPTS=3        # Maximum retry attempts for API calls

# For testing
VITE_AUTH_MODE=test              # Automatically uses mocks
```

## Key Components

### 1. FetchWrapper
Manages HTTP requests with automatic mode selection:
```typescript
// Automatically uses mock or real fetch based on environment
const response = await FetchWrapper.fetch('/api/endpoint', options);

// Configure mock responses for testing
FetchWrapper.addMockResponse('/auth/refresh', {
  status: 200,
  body: { access_token: 'mock-token' }
});
```

### 2. StorageWrapper
Manages localStorage with mock support:
```typescript
// Works in both real and mock modes
StorageWrapper.setItem('key', 'value');
const value = StorageWrapper.getItem('key');

// Enable mock mode for testing
StorageWrapper.setMockMode(true);
```

### 3. BroadcastWrapper
Manages cross-tab communication:
```typescript
// Gets real or mock channel based on environment
const channel = BroadcastWrapper.getChannel('auth-sync');
channel.postMessage({ type: 'TOKEN_REFRESHED' });
```

### 4. TimerWrapper
Manages timers with tracking:
```typescript
// Tracked timers for proper cleanup
const timer = TimerWrapper.setTimeout(callback, 1000);
TimerWrapper.clearTimeout(timer);
```

## Usage Examples

### Development with Real APIs
```bash
# .env.local
VITE_AUTH_MODE=development
VITE_USE_MOCK_AUTH=false
```

### Development with Mock APIs
```bash
# .env.local
VITE_AUTH_MODE=development
VITE_USE_MOCK_AUTH=true
```

### Testing
```typescript
// Tests automatically use mock mode
import { resetAllMocks } from './auth-sync-config';

beforeEach(() => {
  resetAllMocks();
  // Tests run with mocks enabled
});
```

### Production
```bash
# Production automatically uses real APIs
NODE_ENV=production
```

## Benefits

1. **No Global Overwrites**: Never modifies global objects like `fetch` or `localStorage`
2. **Environment-Specific**: Automatically adapts to the environment
3. **Test Isolation**: Tests run in complete isolation with mocks
4. **Easy Debugging**: Can switch to mock mode in development for offline work
5. **Type Safety**: Full TypeScript support for all wrappers
6. **Backward Compatible**: Existing code continues to work

## Migration Guide

### Old Code (Direct Usage)
```typescript
// Before
const token = localStorage.getItem('token');
const response = await fetch('/api/endpoint');
```

### New Code (Wrapper Usage)
```typescript
// After
import { StorageWrapper, FetchWrapper } from './auth-sync-config';

const token = StorageWrapper.getItem('token');
const response = await FetchWrapper.fetch('/api/endpoint');
```

## Testing

### Unit Tests
```typescript
describe('MyComponent', () => {
  beforeEach(() => {
    // Enable mock mode
    StorageWrapper.setMockMode(true);

    // Configure mock responses
    FetchWrapper.addMockResponse('/api/data', {
      status: 200,
      body: { data: 'test' }
    });
  });

  afterEach(() => {
    // Reset all mocks
    resetAllMocks();
  });

  it('should work with mocks', async () => {
    // Test runs with mocks automatically
  });
});
```

### Integration Tests
```typescript
// Can switch between mock and real during tests
StorageWrapper.setMockMode(false); // Use real localStorage
FetchWrapper.configureMock(null);   // Use real fetch
```

## Debugging

Check current configuration:
```typescript
import { AUTH_ENV_INFO } from './auth-sync-config';
console.log('Auth Configuration:', AUTH_ENV_INFO);
```

Output:
```javascript
{
  mode: {
    IS_TEST: false,
    IS_MOCK: false,
    IS_DEVELOPMENT: true,
    IS_PRODUCTION: false
  },
  features: {
    ENABLE_AUTO_REFRESH: true,
    ENABLE_SESSION_MONITORING: true,
    // ...
  },
  timing: {
    TOKEN_REFRESH_THRESHOLD: 5,
    SESSION_TIMEOUT: 30,
    // ...
  },
  endpoints: {
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
    USER_INFO: '/api/v1/users/me'
  }
}
```

## Best Practices

1. **Always use wrappers** instead of direct API calls
2. **Configure environment variables** appropriately for each environment
3. **Reset mocks** in test cleanup to prevent test pollution
4. **Use mock mode** for offline development
5. **Monitor AUTH_ENV_INFO** in development for debugging

## Troubleshooting

### Tests failing with "not a function" errors
- Ensure you're using wrappers instead of mocking globals
- Call `resetAllMocks()` in `beforeEach`

### Mock responses not working
- Check that mock mode is enabled: `AUTH_MODE.IS_MOCK` or `AUTH_MODE.IS_TEST`
- Verify mock response is configured before the request

### Storage not persisting in tests
- This is expected - mock storage is cleared between tests
- Use `StorageWrapper.setMockMode(false)` if you need real persistence

### Cross-tab sync not working
- Check if BroadcastChannel is supported in your browser
- Verify `VITE_ENABLE_CROSS_TAB_SYNC` is true
- In tests, cross-tab sync uses mock channels