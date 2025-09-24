import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  useOptimizedMemo,
  useOptimizedCallback,
  useDebouncedCallback,
  useThrottledCallback,
  useRenderPerformance,
  useComponentLifecycle,
  useMemoizedComputation,
  useIntersectionObserver
} from '../../hooks/usePerformance';
import { setupPerformanceTimers, restoreRealTimers, cleanupTimers } from '../../test/utils/timer-utils';

// Mock console methods for testing
const originalConsole = console;

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

describe('useOptimizedMemo', () => {
  it('memoizes expensive computations', () => {
    const expensiveComputation = vi.fn((x: number) => x * 2);

    const { result, rerender } = renderHook(
      ({ value }) => useOptimizedMemo(() => expensiveComputation(value), [value]),
      { initialProps: { value: 5 } }
    );

    expect(result.current).toBe(10);
    expect(expensiveComputation).toHaveBeenCalledTimes(1);

    // Re-render with same value - should not recompute
    rerender({ value: 5 });
    expect(expensiveComputation).toHaveBeenCalledTimes(1);

    // Re-render with different value - should recompute
    rerender({ value: 10 });
    expect(result.current).toBe(20);
    expect(expensiveComputation).toHaveBeenCalledTimes(2);
  });

  it('logs performance metrics in development', () => {
    // Mock __DEV__ to be true
    (globalThis as any).__DEV__ = true;

    // Setup performance.now() mock sequence before rendering
    vi.spyOn(performance, 'now')
      .mockReturnValueOnce(100) // Start time
      .mockReturnValueOnce(110); // End time (10ms duration)

    const slowComputation = vi.fn(() => {
      return 'result';
    });

    renderHook(() =>
      useOptimizedMemo(() => slowComputation(), [], 'TestMemo')
    );

    expect(console.log).toHaveBeenCalledWith('🧮 TestMemo: 10.00ms');

    (globalThis as any).__DEV__ = false;
  });
});

describe('useOptimizedCallback', () => {
  it('memoizes callback functions', () => {
    const mockFn = vi.fn();

    const { result, rerender } = renderHook(
      ({ deps }) => useOptimizedCallback(mockFn, deps),
      { initialProps: { deps: [1, 2] } }
    );

    const callback1 = result.current;

    // Re-render with same deps - should return same callback
    rerender({ deps: [1, 2] });
    const callback2 = result.current;

    expect(callback1).toBe(callback2);

    // Re-render with different deps - should return new callback
    rerender({ deps: [1, 3] });
    const callback3 = result.current;

    expect(callback1).not.toBe(callback3);
  });

  it('tracks callback execution time', () => {
    (globalThis as any).__DEV__ = true;

    const slowCallback = vi.fn(() => {
      // Callback logic here
    });

    const { result } = renderHook(() =>
      useOptimizedCallback(slowCallback, [], 'TestCallback')
    );

    // Setup performance.now() mock sequence before execution
    vi.spyOn(performance, 'now')
      .mockReturnValueOnce(100) // Start time
      .mockReturnValueOnce(115); // End time (15ms duration)

    act(() => {
      result.current();
    });

    expect(console.log).toHaveBeenCalledWith('⚡ TestCallback: 15.00ms');

    (globalThis as any).__DEV__ = false;
  });
});

describe('useDebouncedCallback', () => {
  // Timer setup handled by global setupPerformanceTimers in parent beforeEach

  it('debounces callback execution', () => {
    const mockFn = vi.fn();

    const { result } = renderHook(() =>
      useDebouncedCallback(mockFn, 300)
    );

    // Call multiple times rapidly
    act(() => {
      result.current();
      result.current();
      result.current();
    });

    // Should not have been called yet
    expect(mockFn).not.toHaveBeenCalled();

    // Fast-forward time
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Should be called only once
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it('cancels debounced callback on unmount', () => {
    const mockFn = vi.fn();

    const { result, unmount } = renderHook(() =>
      useDebouncedCallback(mockFn, 300)
    );

    act(() => {
      result.current();
    });

    // Unmount before delay
    unmount();

    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Should not be called after unmount
    expect(mockFn).not.toHaveBeenCalled();
  });
});

describe('useThrottledCallback', () => {
  // Timer setup handled by global setupPerformanceTimers in parent beforeEach

  it('throttles callback execution', () => {
    const mockFn = vi.fn();

    const { result } = renderHook(() =>
      useThrottledCallback(mockFn, 300)
    );

    // Call multiple times rapidly
    act(() => {
      result.current();
      result.current();
      result.current();
    });

    // Should be called immediately once
    expect(mockFn).toHaveBeenCalledTimes(1);

    // Fast-forward time
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Should be called once more for the throttled calls
    expect(mockFn).toHaveBeenCalledTimes(2);
  });
});

describe('useRenderPerformance', () => {
  beforeEach(() => {
    (globalThis as any).__DEV__ = true;
  });

  afterEach(() => {
    (globalThis as any).__DEV__ = false;
  });

  it('tracks render performance', () => {
    let renderCount = 0;

    const TestComponent = () => {
      useRenderPerformance('TestComponent');
      renderCount++;
      return <div>Render {renderCount}</div>;
    };

    const { rerender } = render(<TestComponent />);

    // Mock slow render
    vi.spyOn(performance, 'now')
      .mockReturnValueOnce(100) // Previous render time
      .mockReturnValueOnce(120); // Current render time (20ms since last)

    rerender(<TestComponent />);

    expect(console.warn).toHaveBeenCalledWith(
      '🐌 TestComponent slow render: 20.00ms (render #2)'
    );
  });

  it('logs total renders on unmount', () => {
    const TestComponent = () => {
      useRenderPerformance('TestComponent');
      return <div>Test</div>;
    };

    const { unmount } = render(<TestComponent />);
    unmount();

    expect(console.log).toHaveBeenCalledWith(
      '📊 TestComponent total renders: 1'
    );
  });
});

describe('useComponentLifecycle', () => {
  beforeEach(() => {
    (globalThis as any).__DEV__ = true;
  });

  afterEach(() => {
    (globalThis as any).__DEV__ = false;
  });

  it('tracks component lifecycle', () => {
    const TestComponent = () => {
      useComponentLifecycle('TestComponent');
      return <div>Test</div>;
    };

    vi.spyOn(performance, 'now')
      .mockReturnValueOnce(100) // Mount time
      .mockReturnValueOnce(150); // Unmount time

    const { unmount } = render(<TestComponent />);

    expect(console.log).toHaveBeenCalledWith('🎬 TestComponent mounted');

    unmount();

    expect(console.log).toHaveBeenCalledWith(
      '🎬 TestComponent unmounted after 50.00ms'
    );
  });
});

describe('useMemoizedComputation', () => {
  it('caches computation results', () => {
    const expensiveComputation = vi.fn((x: number, y: number) => x + y);

    const { result } = renderHook(() =>
      useMemoizedComputation(expensiveComputation, 5)
    );

    // First call
    const result1 = result.current(10, 20);
    expect(result1).toBe(30);
    expect(expensiveComputation).toHaveBeenCalledTimes(1);

    // Same arguments - should use cache
    const result2 = result.current(10, 20);
    expect(result2).toBe(30);
    expect(expensiveComputation).toHaveBeenCalledTimes(1);

    // Different arguments - should compute again
    const result3 = result.current(15, 25);
    expect(result3).toBe(40);
    expect(expensiveComputation).toHaveBeenCalledTimes(2);
  });

  it('implements LRU cache with size limit', () => {
    const computation = vi.fn((x: number) => x * 2);

    const { result } = renderHook(() =>
      useMemoizedComputation(computation, 2) // Max cache size of 2
    );

    // Fill cache
    result.current(1); // Cache: [1]
    result.current(2); // Cache: [1, 2]
    result.current(3); // Cache: [2, 3] (1 evicted)

    expect(computation).toHaveBeenCalledTimes(3);

    // Access 1 again - should recompute (was evicted)
    result.current(1);
    expect(computation).toHaveBeenCalledTimes(4);

    // Access 3 again - should use cache (still in cache)
    result.current(3);
    expect(computation).toHaveBeenCalledTimes(4);
  });
});

describe('useIntersectionObserver', () => {
  beforeEach(() => {
    // Mock IntersectionObserver
    global.IntersectionObserver = vi.fn((callback) => ({
      observe: vi.fn(),
      disconnect: vi.fn(),
      unobserve: vi.fn()
    })) as any;
  });

  it('sets up intersection observer', () => {
    const { result } = renderHook(() =>
      useIntersectionObserver({ threshold: 0.5 })
    );

    expect(result.current.ref).toBeDefined();
    expect(result.current.isIntersecting).toBe(false);
    expect(result.current.entry).toBe(null);
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

    const { result, rerender } = renderHook(() =>
      useIntersectionObserver({ threshold: 0.5 })
    );

    // Create and set a ref element to trigger observation
    const mockElement = document.createElement('div');
    Object.defineProperty(result.current.ref, 'current', {
      writable: true,
      value: mockElement
    });

    // Force a rerender to trigger the effect
    rerender();

    // Verify IntersectionObserver was created
    expect(mockIntersectionObserver).toHaveBeenCalled();
    expect(mockObserver.observe).toHaveBeenCalledWith(mockElement);
  });
});

describe('Performance Hook Integration', () => {
  it('works together in a real component', () => {
    const TestComponent: React.FunctionComponent<{ items: number[] }> = ({ items }) => {
      useRenderPerformance('TestComponent');
      useComponentLifecycle('TestComponent');

      const expensiveComputation = useMemoizedComputation(
        (items: number[]) => items.reduce((sum, item) => sum + item, 0),
        10
      );

      const debouncedLog = useDebouncedCallback(
        (message: string) => console.log(message),
        300
      );

      const sum = useOptimizedMemo(
        () => expensiveComputation(items),
        [items, expensiveComputation],
        'sum-calculation'
      );

      const handleClick = useOptimizedCallback(() => {
        debouncedLog(`Sum is ${sum}`);
      }, [sum, debouncedLog], 'handle-click');

      return (
        <div>
          <span data-testid="sum">{sum}</span>
          <button onClick={(e: React.MouseEvent) => handleClick}>Log Sum</button>
        </div>
      );
    };

    const { rerender } = render(<TestComponent items={[1, 2, 3]} />);

    expect(screen.getByTestId('sum')).toHaveTextContent('6');

    // Rerender with same items - should use memoized result
    rerender(<TestComponent items={[1, 2, 3]} />);
    expect(screen.getByTestId('sum')).toHaveTextContent('6');

    // Rerender with different items - should recompute
    rerender(<TestComponent items={[1, 2, 3, 4]} />);
    expect(screen.getByTestId('sum')).toHaveTextContent('10');
  });
});