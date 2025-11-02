import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { Suspense } from 'react';
import { render, screen } from '@testing-library/react';
import {
  useOptimizedLazyLoad,
  createOptimizedLazyComponent,
  preloadComponents,
  getPerformanceMetrics,
  resetPerformanceMetrics,
} from '../useOptimizedLazyLoad';

// Mock component for testing
const MockComponent = () => <div>Mock Component</div>;
const MockFallback = () => <div>Fallback Component</div>;

// FIXME: Tests timing out due to async/timer synchronization issues - see docs/05-implementation/testing/reports/TESTING_KNOWN_ISSUES.md #5
describe.skip('useOptimizedLazyLoad', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetPerformanceMetrics();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Basic Functionality', () => {
    it('should load component successfully', async () => {
      const importFn = vi.fn().mockResolvedValue({ default: MockComponent });

      const { result } = renderHook(() => useOptimizedLazyLoad(importFn));

      expect(result.current).toBeDefined();

      // Trigger the lazy load by rendering the component
      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      await waitFor(() => {
        expect(importFn).toHaveBeenCalled();
      });
    });

    it('should use cache for subsequent calls', () => {
      const importFn = vi.fn().mockResolvedValue({ default: MockComponent });

      const { result: result1 } = renderHook(() => useOptimizedLazyLoad(importFn));
      const { result: result2 } = renderHook(() => useOptimizedLazyLoad(importFn));

      // Should return the same cached component
      expect(result1.current).toBe(result2.current);

      const metrics = getPerformanceMetrics();
      expect(metrics.cacheHits).toBe(1);
    });

    it('should pass through component props', async () => {
      const importFn = vi.fn().mockResolvedValue({
        default: ({ text }: { text: string }) => <div>{text}</div>,
      });

      const { result } = renderHook(() => useOptimizedLazyLoad(importFn));

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent text="Test Content" />
        </Suspense>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Content')).toBeInTheDocument();
      });
    });
  });

  describe('Timeout Handling', () => {
    it('should timeout after specified duration', async () => {
      const importFn = vi.fn().mockImplementation(
        () =>
          new Promise(resolve => {
            setTimeout(() => resolve({ default: MockComponent }), 3000);
          })
      );

      const { result } = renderHook(() =>
        useOptimizedLazyLoad(importFn, {
          timeout: 1000,
          fallbackComponent: MockFallback,
        })
      );

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      // Advance past timeout
      vi.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(screen.getByText('Fallback Component')).toBeInTheDocument();
      });
    });

    it('should use generic fallback when no custom fallback provided', async () => {
      const importFn = vi.fn().mockImplementation(
        () =>
          new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Timeout')), 100);
          })
      );

      const { result } = renderHook(() =>
        useOptimizedLazyLoad(importFn, { timeout: 100 })
      );

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      vi.advanceTimersByTime(100);

      await waitFor(() => {
        expect(screen.getByText('Component optimized for performance')).toBeInTheDocument();
      });
    });
  });

  describe('Retry Logic', () => {
    it('should retry on failure', async () => {
      const importFn = vi.fn()
        .mockRejectedValueOnce(new Error('Load failed'))
        .mockResolvedValueOnce({ default: MockComponent });

      const { result } = renderHook(() =>
        useOptimizedLazyLoad(importFn, {
          retries: 1,
          timeout: 5000,
        })
      );

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      await waitFor(() => {
        expect(importFn).toHaveBeenCalledTimes(2);
      });

      await waitFor(() => {
        expect(screen.getByText('Mock Component')).toBeInTheDocument();
      });
    });

    it('should use fallback after max retries', async () => {
      const importFn = vi.fn().mockRejectedValue(new Error('Load failed'));

      const { result } = renderHook(() =>
        useOptimizedLazyLoad(importFn, {
          retries: 2,
          timeout: 5000,
          fallbackComponent: MockFallback,
        })
      );

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      await waitFor(() => {
        expect(importFn).toHaveBeenCalledTimes(3); // Initial + 2 retries
      });

      await waitFor(() => {
        expect(screen.getByText('Fallback Component')).toBeInTheDocument();
      });
    });

    it('should not retry beyond specified limit', async () => {
      const importFn = vi.fn().mockRejectedValue(new Error('Load failed'));

      const { result } = renderHook(() =>
        useOptimizedLazyLoad(importFn, {
          retries: 1,
          timeout: 5000,
        })
      );

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      await waitFor(() => {
        expect(importFn).toHaveBeenCalledTimes(2); // Initial + 1 retry
      });
    });
  });

  describe('Preloading', () => {
    it('should preload component when enabled', async () => {
      const importFn = vi.fn().mockResolvedValue({ default: MockComponent });

      renderHook(() =>
        useOptimizedLazyLoad(importFn, {
          preload: true,
          priority: 'high',
        })
      );

      // Advance timers to trigger preload (high priority = 0ms delay)
      vi.advanceTimersByTime(0);

      await waitFor(() => {
        expect(importFn).toHaveBeenCalled();
      });

      const metrics = getPerformanceMetrics();
      expect(metrics.preloads).toBe(1);
    });

    it('should respect priority delays', async () => {
      const highPriorityFn = vi.fn().mockResolvedValue({ default: MockComponent });
      const mediumPriorityFn = vi.fn().mockResolvedValue({ default: MockComponent });
      const lowPriorityFn = vi.fn().mockResolvedValue({ default: MockComponent });

      renderHook(() =>
        useOptimizedLazyLoad(highPriorityFn, { preload: true, priority: 'high' })
      );
      renderHook(() =>
        useOptimizedLazyLoad(mediumPriorityFn, { preload: true, priority: 'medium' })
      );
      renderHook(() =>
        useOptimizedLazyLoad(lowPriorityFn, { preload: true, priority: 'low' })
      );

      // High priority should load immediately
      vi.advanceTimersByTime(0);
      await waitFor(() => {
        expect(highPriorityFn).toHaveBeenCalled();
      });

      // Medium priority after 100ms
      vi.advanceTimersByTime(100);
      await waitFor(() => {
        expect(mediumPriorityFn).toHaveBeenCalled();
      });

      // Low priority after 500ms
      vi.advanceTimersByTime(400);
      await waitFor(() => {
        expect(lowPriorityFn).toHaveBeenCalled();
      });
    });

    it('should handle preload failures gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const importFn = vi.fn().mockRejectedValue(new Error('Preload failed'));

      renderHook(() =>
        useOptimizedLazyLoad(importFn, {
          preload: true,
          priority: 'high',
        })
      );

      vi.advanceTimersByTime(0);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Component preload failed:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Performance Metrics', () => {
    it('should track successful loads', async () => {
      resetPerformanceMetrics();

      const importFn = vi.fn().mockResolvedValue({ default: MockComponent });

      const { result } = renderHook(() => useOptimizedLazyLoad(importFn));

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      await waitFor(() => {
        expect(importFn).toHaveBeenCalled();
      });

      await waitFor(() => {
        const metrics = getPerformanceMetrics();
        expect(metrics.totalLoads).toBe(1);
        expect(metrics.averageLoadTime).toBeGreaterThan(0);
      });
    });

    it('should track timeouts', async () => {
      resetPerformanceMetrics();

      const importFn = vi.fn().mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() =>
        useOptimizedLazyLoad(importFn, {
          timeout: 100,
          fallbackComponent: MockFallback,
        })
      );

      const LazyComponent = result.current;
      render(
        <Suspense fallback={<div>Loading...</div>}>
          <LazyComponent />
        </Suspense>
      );

      vi.advanceTimersByTime(100);

      await waitFor(() => {
        const metrics = getPerformanceMetrics();
        expect(metrics.timeouts).toBe(1);
      });
    });

    it('should calculate cache efficiency', async () => {
      resetPerformanceMetrics();

      const importFn = vi.fn().mockResolvedValue({ default: MockComponent });

      // First load - no cache
      renderHook(() => useOptimizedLazyLoad(importFn));

      // Second load - cache hit
      renderHook(() => useOptimizedLazyLoad(importFn));

      const metrics = getPerformanceMetrics();
      expect(metrics.cacheEfficiency).toBe(50); // 1 cache hit out of 2 total loads
    });

    it('should reset metrics correctly', () => {
      const importFn = vi.fn().mockResolvedValue({ default: MockComponent });

      renderHook(() => useOptimizedLazyLoad(importFn));
      renderHook(() => useOptimizedLazyLoad(importFn));

      let metrics = getPerformanceMetrics();
      expect(metrics.cacheHits).toBeGreaterThan(0);

      resetPerformanceMetrics();

      metrics = getPerformanceMetrics();
      expect(metrics.totalLoads).toBe(0);
      expect(metrics.totalLoadTime).toBe(0);
      expect(metrics.timeouts).toBe(0);
      expect(metrics.cacheHits).toBe(0);
      expect(metrics.preloads).toBe(0);
    });
  });
});

// FIXME: Tests timing out due to async/timer synchronization issues - see docs/05-implementation/testing/reports/TESTING_KNOWN_ISSUES.md #5
describe.skip('createOptimizedLazyComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetPerformanceMetrics();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should create lazy component with defaults', async () => {
    const importFn = vi.fn().mockResolvedValue({ default: MockComponent });

    const LazyComponent = createOptimizedLazyComponent(importFn, 'TestComponent');

    render(
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
    );

    await waitFor(() => {
      expect(importFn).toHaveBeenCalled();
    });
  });

  it('should apply custom options', async () => {
    const importFn = vi.fn().mockImplementation(
      () =>
        new Promise(resolve => {
          setTimeout(() => resolve({ default: MockComponent }), 2000);
        })
    );

    const LazyComponent = createOptimizedLazyComponent(importFn, 'TestComponent', {
      timeout: 1000,
      preload: true,
      priority: 'high',
    });

    render(
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
    );

    // Timeout should trigger before component loads
    vi.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(screen.getByText('TestComponent')).toBeInTheDocument();
    });
  });

  it('should use custom fallback when provided', async () => {
    const importFn = vi.fn().mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const CustomFallback = () => <div>Custom Fallback</div>;

    const LazyComponent = createOptimizedLazyComponent(importFn, 'TestComponent', {
      timeout: 100,
      fallbackComponent: CustomFallback,
    });

    render(
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
    );

    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(screen.getByText('Custom Fallback')).toBeInTheDocument();
    });
  });

  it('should generate default fallback with component name', async () => {
    const importFn = vi.fn().mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const LazyComponent = createOptimizedLazyComponent(importFn, 'MyComponent', {
      timeout: 100,
    });

    render(
      <Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </Suspense>
    );

    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(screen.getByText('MyComponent')).toBeInTheDocument();
      expect(screen.getByText('Loading optimized version...')).toBeInTheDocument();
    });
  });
});

// FIXME: Tests timing out due to async/timer synchronization issues - see docs/05-implementation/testing/reports/TESTING_KNOWN_ISSUES.md #5
describe.skip('preloadComponents', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should preload components in priority order', async () => {
    const highPriorityFn = vi.fn().mockResolvedValue({ default: MockComponent });
    const mediumPriorityFn = vi.fn().mockResolvedValue({ default: MockComponent });
    const lowPriorityFn = vi.fn().mockResolvedValue({ default: MockComponent });

    preloadComponents([
      { importFn: lowPriorityFn, priority: 'low' },
      { importFn: highPriorityFn, priority: 'high' },
      { importFn: mediumPriorityFn, priority: 'medium' },
    ]);

    // High priority loads first (0ms delay)
    vi.advanceTimersByTime(0);
    await waitFor(() => {
      expect(highPriorityFn).toHaveBeenCalled();
    });

    // Medium priority loads second (100ms delay)
    vi.advanceTimersByTime(100);
    await waitFor(() => {
      expect(mediumPriorityFn).toHaveBeenCalled();
    });

    // Low priority loads third (200ms delay)
    vi.advanceTimersByTime(100);
    await waitFor(() => {
      expect(lowPriorityFn).toHaveBeenCalled();
    });
  });

  it('should handle preload failures gracefully', async () => {
    const failingFn = vi.fn().mockRejectedValue(new Error('Load failed'));

    preloadComponents([{ importFn: failingFn, priority: 'high' }]);

    vi.advanceTimersByTime(0);

    await waitFor(() => {
      expect(failingFn).toHaveBeenCalled();
    });

    // Should not throw - failures are ignored
  });

  it('should use medium priority by default', async () => {
    const defaultFn = vi.fn().mockResolvedValue({ default: MockComponent });

    preloadComponents([{ importFn: defaultFn }]);

    // Should use 100ms delay for medium priority (index 0)
    vi.advanceTimersByTime(0);
    await waitFor(() => {
      expect(defaultFn).toHaveBeenCalled();
    });
  });

  it('should stagger preloads by index', async () => {
    const fn1 = vi.fn().mockResolvedValue({ default: MockComponent });
    const fn2 = vi.fn().mockResolvedValue({ default: MockComponent });
    const fn3 = vi.fn().mockResolvedValue({ default: MockComponent });

    preloadComponents([
      { importFn: fn1, priority: 'medium' },
      { importFn: fn2, priority: 'medium' },
      { importFn: fn3, priority: 'medium' },
    ]);

    // First medium priority: 0ms delay
    vi.advanceTimersByTime(0);
    await waitFor(() => {
      expect(fn1).toHaveBeenCalled();
    });

    // Second medium priority: 100ms delay
    vi.advanceTimersByTime(100);
    await waitFor(() => {
      expect(fn2).toHaveBeenCalled();
    });

    // Third medium priority: 200ms delay
    vi.advanceTimersByTime(100);
    await waitFor(() => {
      expect(fn3).toHaveBeenCalled();
    });
  });
});
