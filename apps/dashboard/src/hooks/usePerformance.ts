import { useCallback, useMemo, useRef, useEffect, useState } from 'react';

// Simple debounce implementation
function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T & { cancel: () => void } {
  let timeoutId: NodeJS.Timeout | null = null;

  const debounced = ((...args: Parameters<T>) => {
    if (timeoutId) clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  }) as T & { cancel: () => void };

  debounced.cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  return debounced;
}

// Simple throttle implementation
function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T & { cancel: () => void } {
  let lastCall = 0;
  let timeoutId: NodeJS.Timeout | null = null;

  const throttled = ((...args: Parameters<T>) => {
    const now = Date.now();

    if (now - lastCall >= delay) {
      lastCall = now;
      return func(...args);
    } else if (!timeoutId) {
      timeoutId = setTimeout(() => {
        lastCall = Date.now();
        timeoutId = null;
        func(...args);
      }, delay - (now - lastCall));
    }
  }) as T & { cancel: () => void };

  throttled.cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  return throttled;
}

/**
 * Enhanced useMemo with performance tracking
 */
export function useOptimizedMemo<T>(
  factory: () => T,
  deps: React.DependencyList,
  debugName?: string
): T {
  const startTime = useRef<number>();

  return useMemo(() => {
    if (__DEV__ && debugName) {
      startTime.current = performance.now();
    }

    const result = factory();

    if (__DEV__ && debugName && startTime.current) {
      const duration = performance.now() - startTime.current;
      if (duration > 5) { // Log if computation takes more than 5ms
        console.log(`🧮 ${debugName}: ${duration.toFixed(2)}ms`);
      }
    }

    return result;
  }, deps);
}

/**
 * Enhanced useCallback with performance tracking
 */
export function useOptimizedCallback<T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList,
  debugName?: string
): T {
  return useCallback((...args: Parameters<T>) => {
    const startTime = __DEV__ && debugName ? performance.now() : 0;

    const result = callback(...args);

    if (__DEV__ && debugName && startTime) {
      const duration = performance.now() - startTime;
      if (duration > 10) { // Log if callback takes more than 10ms
        console.log(`⚡ ${debugName}: ${duration.toFixed(2)}ms`);
      }
    }

    return result;
  }, deps) as T;
}

/**
 * Debounced callback hook
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const debouncedCallback = useMemo(
    () => debounce(callback, delay),
    [callback, delay, ...deps]
  );

  useEffect(() => {
    return () => {
      debouncedCallback.cancel();
    };
  }, [debouncedCallback]);

  return debouncedCallback as T;
}

/**
 * Throttled callback hook
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const throttledCallback = useMemo(
    () => throttle(callback, delay),
    [callback, delay, ...deps]
  );

  useEffect(() => {
    return () => {
      throttledCallback.cancel();
    };
  }, [throttledCallback]);

  return throttledCallback as T;
}

/**
 * Hook for measuring component render performance
 */
export function useRenderPerformance(componentName: string, enabled = __DEV__) {
  const renderCount = useRef(0);
  const lastRenderTime = useRef(performance.now());

  useEffect(() => {
    if (!enabled) return;

    renderCount.current++;
    const now = performance.now();
    const timeSinceLastRender = now - lastRenderTime.current;
    lastRenderTime.current = now;

    if (timeSinceLastRender > 16.67) { // Slower than 60fps
      console.warn(`🐌 ${componentName} slow render: ${timeSinceLastRender.toFixed(2)}ms (render #${renderCount.current})`);
    }
  });

  useEffect(() => {
    if (!enabled) return;

    return () => {
      console.log(`📊 ${componentName} total renders: ${renderCount.current}`);
    };
  }, [componentName, enabled]);
}

/**
 * Hook for tracking component mount/unmount times
 */
export function useComponentLifecycle(componentName: string, enabled = __DEV__) {
  const mountTime = useRef<number>();

  useEffect(() => {
    if (!enabled) return;

    mountTime.current = performance.now();
    console.log(`🎬 ${componentName} mounted`);

    return () => {
      if (mountTime.current) {
        const lifetime = performance.now() - mountTime.current;
        console.log(`🎬 ${componentName} unmounted after ${lifetime.toFixed(2)}ms`);
      }
    };
  }, [componentName, enabled]);
}

/**
 * Hook for memoizing expensive computations with cache size limit
 */
export function useMemoizedComputation<T, Args extends readonly unknown[]>(
  computation: (...args: Args) => T,
  maxCacheSize = 10
) {
  const cache = useRef(new Map<string, T>());

  return useCallback((...args: Args): T => {
    const key = JSON.stringify(args);

    if (cache.current.has(key)) {
      return cache.current.get(key)!;
    }

    const result = computation(...args);

    // Implement LRU cache
    if (cache.current.size >= maxCacheSize) {
      const firstKey = cache.current.keys().next().value;
      cache.current.delete(firstKey);
    }

    cache.current.set(key, result);
    return result;
  }, [computation, maxCacheSize]);
}

/**
 * Hook for lazy loading components with error boundary
 */
export function useLazyComponent<T = React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) {
  const [component, setComponent] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    importFn()
      .then((module) => {
        if (mounted) {
          setComponent(module.default);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err);
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [importFn]);

  return { component, loading, error };
}

/**
 * Hook for intersection observer with performance optimizations
 */
export function useIntersectionObserver(
  options: IntersectionObserverInit = {},
  triggerOnce = true
) {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const elementRef = useRef<Element | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const cleanup = useCallback(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!elementRef.current) return;

    cleanup();

    observerRef.current = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        setEntry(entry);
        setIsIntersecting(entry.isIntersecting);

        if (triggerOnce && entry.isIntersecting) {
          cleanup();
        }
      },
      options
    );

    observerRef.current.observe(elementRef.current);

    return cleanup;
  }, [cleanup, triggerOnce, options]);

  return { ref: elementRef, isIntersecting, entry };
}

export default {
  useOptimizedMemo,
  useOptimizedCallback,
  useDebouncedCallback,
  useThrottledCallback,
  useRenderPerformance,
  useComponentLifecycle,
  useMemoizedComputation,
  useLazyComponent,
  useIntersectionObserver
};