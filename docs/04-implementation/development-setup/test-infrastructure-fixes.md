# Test Infrastructure Fixes: Timer Mock Conflicts Resolution

## Overview

This document details the comprehensive fixes implemented to resolve timer mock conflicts in the ToolBoxAI-Solutions dashboard test suite. The fixes eliminated "Timers are not mocked" errors and improved test reliability by creating a centralized timer management system.

## Problem Statement

### Issues Identified

1. **Timer Mock Conflicts**: Global timer mocking in test setup caused conflicts between tests requiring different timer configurations
2. **Performance Test Failures**: 4 out of 15 performance tests were failing due to improper timer mock order
3. **IntersectionObserver Setup Issues**: Mock setup conflicts prevented proper observer initialization
4. **LRU Cache Test Expectations**: Incorrect expectations about cache behavior during timer operations

### Error Symptoms

```bash
# Common errors before fixes:
Error: Timers are not mocked. You must call vi.useFakeTimers() first.
TypeError: Cannot read properties of undefined (reading 'now')
AssertionError: expected 4 to be 3 # LRU cache eviction timing
```

## Solution Architecture

### 1. Centralized Timer Management Utility

Created `/apps/dashboard/src/test/utils/timer-utils.ts` to provide standardized timer mock management:

```typescript
/**
 * Timer Utilities for Test Environment
 * Provides centralized timer mock management to prevent conflicts
 */

export interface TimerConfig {
  /** Whether to include performance.now() in mocks */
  includePerformance?: boolean;
  /** Whether time should automatically advance */
  shouldAdvanceTime?: boolean;
  /** Custom list of timer methods to fake */
  toFake?: string[];
}

// Predefined configurations for different test types
const DEFAULT_CONFIG: TimerConfig = {
  includePerformance: false,
  shouldAdvanceTime: true,
  toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date']
};

const PERFORMANCE_CONFIG: TimerConfig = {
  includePerformance: true,
  shouldAdvanceTime: false,
  toFake: [
    'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval',
    'Date', 'performance'
  ]
};
```

### 2. State Tracking and Conflict Prevention

```typescript
// Track current timer state to prevent conflicts
let currentTimerState: 'real' | 'fake' | 'uninitialized' = 'uninitialized';

export function setupFakeTimers(config: TimerConfig = {}): void {
  // If timers are already fake, restore them first to prevent conflicts
  if (currentTimerState === 'fake') {
    vi.useRealTimers();
  }

  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  vi.useFakeTimers({
    shouldAdvanceTime: finalConfig.shouldAdvanceTime,
    toFake: finalConfig.toFake as any
  });

  currentTimerState = 'fake';
}
```

### 3. Specialized Timer Configurations

```typescript
// Performance test timer configuration
export function setupPerformanceTimers(): void {
  setupFakeTimers(PERFORMANCE_CONFIG);
}

// Helper for running async code with fake timers
export async function withPerformanceTimers<T>(
  fn: () => Promise<T>
): Promise<T> {
  return withFakeTimers(fn, PERFORMANCE_CONFIG);
}
```

## Implementation Details

### Modified Test Setup (`/apps/dashboard/src/test/setup.ts`)

**Before**: Global timer mocking that caused conflicts
```typescript
// OLD: Caused conflicts between tests
beforeAll(() => {
  vi.useFakeTimers(); // Global timer mocking
});
```

**After**: Removed global timer mocking, delegated to per-test management
```typescript
beforeAll(() => {
  // Set test environment
  process.env.NODE_ENV = 'test';

  // Note: Timer mocking is now handled per-test using timer-utils.ts
  // This prevents conflicts between tests that need different timer configurations

  // Start MSW server
  server.listen({
    onUnhandledRequest: 'bypass',
  });
});
```

### Updated Performance Tests (`/apps/dashboard/src/__tests__/performance/usePerformance.test.tsx`)

**Before**: Manual timer setup with conflicts
```typescript
beforeEach(() => {
  vi.useFakeTimers(); // Could conflict with global setup
  vi.spyOn(performance, 'now').mockReturnValue(100);
});
```

**After**: Centralized timer management
```typescript
import {
  setupPerformanceTimers,
  restoreRealTimers,
  cleanupTimers
} from '../../test/utils/timer-utils';

beforeEach(() => {
  // Setup performance timers that include performance.now() mocking
  setupPerformanceTimers();

  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(performance, 'now').mockReturnValue(100);
});

afterEach(() => {
  // Clean up timers and restore real timers
  cleanupTimers();
  restoreRealTimers();
  vi.restoreAllMocks();
});
```

## Key Fixes Applied

### 1. Performance.now() Mock Order

**Problem**: Performance.now() mocks were applied in wrong order causing timing calculation errors.

**Solution**: Proper mock sequencing for timing scenarios
```typescript
it('logs performance metrics in development', () => {
  (globalThis as any).__DEV__ = true;

  // Setup performance.now() mock sequence before rendering
  vi.spyOn(performance, 'now')
    .mockReturnValueOnce(100) // Start time
    .mockReturnValueOnce(110); // End time (10ms duration)

  const slowComputation = vi.fn(() => 'result');

  renderHook(() =>
    useOptimizedMemo(() => slowComputation(), [], 'TestMemo')
  );

  expect(console.log).toHaveBeenCalledWith('🧮 TestMemo: 10.00ms');
});
```

### 2. LRU Cache Test Corrections

**Problem**: Cache eviction expectations didn't account for timer behavior.

**Solution**: Updated test expectations to match actual cache behavior
```typescript
it('implements LRU cache with size limit', () => {
  const computation = vi.fn((x: number) => x * 2);

  const { result } = renderHook(() =>
    useMemoizedComputation(computation, 2) // Max cache size of 2
  );

  // Fill cache with proper expectations
  result.current(1); // Cache: [1]
  result.current(2); // Cache: [1, 2]
  result.current(3); // Cache: [2, 3] (1 evicted)

  expect(computation).toHaveBeenCalledTimes(3);

  // Access 1 again - should recompute (was evicted)
  result.current(1);
  expect(computation).toHaveBeenCalledTimes(4); // Updated expectation

  // Access 3 again - should use cache (still in cache)
  result.current(3);
  expect(computation).toHaveBeenCalledTimes(4); // Stays at 4
});
```

### 3. IntersectionObserver Mock Setup

**Problem**: Mock conflicts prevented proper observer initialization.

**Solution**: Isolated mock setup per test
```typescript
describe('useIntersectionObserver', () => {
  beforeEach(() => {
    // Fresh mock for each test to prevent conflicts
    global.IntersectionObserver = vi.fn((callback) => ({
      observe: vi.fn(),
      disconnect: vi.fn(),
      unobserve: vi.fn()
    })) as any;
  });

  it('triggers callback when element intersects', () => {
    const mockObserver = {
      observe: vi.fn(),
      disconnect: vi.fn(),
      unobserve: vi.fn()
    };

    const mockCallback = vi.fn();
    const mockIntersectionObserver = vi.fn((callback) => {
      mockCallback.mockImplementation(callback);
      return mockObserver;
    });

    global.IntersectionObserver = mockIntersectionObserver as any;
    // ... rest of test
  });
});
```

## Utility Functions Reference

### Timer Management Functions

```typescript
// Basic timer setup
setupFakeTimers(config?: TimerConfig): void

// Performance-specific setup
setupPerformanceTimers(): void

// Cleanup and restoration
restoreRealTimers(): void
cleanupTimers(): void

// Timer manipulation
advanceTimersByTime(ms: number): void
runAllTimers(): void

// State inspection
getTimerState(): 'real' | 'fake' | 'uninitialized'

// Helper wrappers
withFakeTimers<T>(fn: () => Promise<T>, config?: TimerConfig): Promise<T>
withPerformanceTimers<T>(fn: () => Promise<T>): Promise<T>
```

### Configuration Options

```typescript
interface TimerConfig {
  includePerformance?: boolean;  // Include performance.now() in mocks
  shouldAdvanceTime?: boolean;   // Auto-advance time
  toFake?: string[];            // Custom timer methods to mock
}

// Predefined configurations
DEFAULT_CONFIG        // Basic timers, auto-advance
PERFORMANCE_CONFIG    // Includes performance.now(), manual advance
```

## Best Practices for Future Tests

### 1. Use Appropriate Timer Configuration

```typescript
// For basic component tests
beforeEach(() => {
  setupFakeTimers(); // Uses DEFAULT_CONFIG
});

// For performance tests
beforeEach(() => {
  setupPerformanceTimers(); // Uses PERFORMANCE_CONFIG
});

// For custom needs
beforeEach(() => {
  setupFakeTimers({
    includePerformance: true,
    shouldAdvanceTime: false,
    toFake: ['setTimeout', 'performance']
  });
});
```

### 2. Proper Cleanup

```typescript
afterEach(() => {
  cleanupTimers();    // Clear pending timers
  restoreRealTimers(); // Restore real timers
  vi.restoreAllMocks(); // Restore all mocks
});
```

### 3. Mock Sequencing for Performance Tests

```typescript
// Setup mock sequence before the operation
vi.spyOn(performance, 'now')
  .mockReturnValueOnce(startTime)
  .mockReturnValueOnce(endTime);

// Then perform the operation
const result = performOperation();

// Then assert
expect(console.log).toHaveBeenCalledWith(`Operation: ${expectedDuration}ms`);
```

### 4. Timer-Dependent Assertions

```typescript
// For debounced operations
act(() => {
  debouncedFunction();
});

// Verify not called immediately
expect(mockFn).not.toHaveBeenCalled();

// Advance time and verify call
act(() => {
  vi.advanceTimersByTime(delayMs);
});
expect(mockFn).toHaveBeenCalledTimes(1);
```

## Test Results

### Before Fixes
```bash
✓ 11 passing
✗ 4 failing

Failures:
- useMemoizedComputation LRU cache test
- useOptimizedMemo performance logging
- useOptimizedCallback execution tracking
- useIntersectionObserver callback triggering
```

### After Fixes
```bash
✓ 15 passing
✗ 0 failing

All performance tests now pass:
- Timer mock conflicts resolved
- Performance.now() mocking order fixed
- LRU cache expectations corrected
- IntersectionObserver setup stabilized
```

## Migration Guide

### For Existing Tests

1. **Remove manual timer setup** in test files:
   ```typescript
   // Remove these lines
   vi.useFakeTimers();
   vi.useRealTimers();
   ```

2. **Import timer utilities**:
   ```typescript
   import {
     setupFakeTimers,
     setupPerformanceTimers,
     restoreRealTimers,
     cleanupTimers
   } from '../test/utils/timer-utils';
   ```

3. **Use appropriate setup in beforeEach**:
   ```typescript
   beforeEach(() => {
     setupFakeTimers(); // or setupPerformanceTimers() for performance tests
   });
   ```

4. **Add proper cleanup in afterEach**:
   ```typescript
   afterEach(() => {
     cleanupTimers();
     restoreRealTimers();
     vi.restoreAllMocks();
   });
   ```

### For New Tests

1. **Choose appropriate timer configuration** based on test needs
2. **Use the helper functions** for common timer operations
3. **Follow the cleanup pattern** consistently
4. **Leverage wrapper functions** like `withPerformanceTimers()` for isolated operations

## Troubleshooting

### Common Issues

1. **"Timers are not mocked" error**:
   - Ensure `setupFakeTimers()` is called before timer operations
   - Check that cleanup is properly called in `afterEach`

2. **Performance.now() undefined**:
   - Use `setupPerformanceTimers()` instead of `setupFakeTimers()`
   - Verify mock sequencing for timing assertions

3. **Timer conflicts between tests**:
   - Ensure `cleanupTimers()` and `restoreRealTimers()` are called in cleanup
   - Check for leftover timer mocks from previous tests

4. **Unexpected timer behavior**:
   - Verify timer configuration matches test requirements
   - Use `getTimerState()` to inspect current timer state

### Debug Tips

```typescript
// Check current timer state
console.log('Timer state:', getTimerState());

// Verify timer configuration
setupFakeTimers({
  includePerformance: true,
  shouldAdvanceTime: false,
  toFake: ['setTimeout', 'performance']
});

// Use wrapper for isolation
await withPerformanceTimers(async () => {
  // Test code here is isolated
});
```

## Impact and Benefits

1. **Test Reliability**: All 15 performance tests now pass consistently
2. **Maintainability**: Centralized timer management reduces code duplication
3. **Debugging**: Clear error messages and state tracking
4. **Flexibility**: Easy to configure timers for different test scenarios
5. **Isolation**: Tests don't interfere with each other's timer state

## Future Considerations

1. **Performance Monitoring**: Consider adding performance benchmarks to CI
2. **Test Coverage**: Add timer utility tests to ensure reliability
3. **Documentation**: Keep this guide updated as timer utilities evolve
4. **Integration**: Consider similar patterns for other test utilities

This comprehensive fix resolves the timer mock conflicts and provides a robust foundation for future test development in the ToolBoxAI dashboard.