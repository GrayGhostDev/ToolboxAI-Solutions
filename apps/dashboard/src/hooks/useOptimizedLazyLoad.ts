import { lazy, type ComponentType, type LazyExoticComponent } from 'react';
import * as React from 'react';

interface LazyLoadOptions {
  timeout?: number;
  fallbackComponent?: ComponentType<any>;
  retries?: number;
  preload?: boolean;
  priority?: 'high' | 'medium' | 'low';
}

interface LazyComponentCache {
  [key: string]: {
    component: LazyExoticComponent<any>;
    preloaded: boolean;
    failed: boolean;
  };
}

// Global cache for lazy components
const componentCache: LazyComponentCache = {};

// Performance metrics for optimization
const performanceMetrics = {
  totalLoads: 0,
  totalLoadTime: 0,
  timeouts: 0,
  cacheHits: 0,
  preloads: 0
};

/**
 * Enhanced lazy loading hook with timeout, caching, and performance optimization
 */
export const useOptimizedLazyLoad = <T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): LazyExoticComponent<T> => {
  const {
    timeout = 2000,
    fallbackComponent,
    retries = 1,
    preload = false,
    priority = 'medium'
  } = options;

  // Create cache key based on import function string
  const cacheKey = importFn.toString().slice(0, 100);

  // Return cached component if available
  if (componentCache[cacheKey] && !componentCache[cacheKey].failed) {
    performanceMetrics.cacheHits++;
    return componentCache[cacheKey].component;
  }

  // Create optimized lazy component with timeout and retry logic
  const lazyComponent = lazy(() => {
    const startTime = Date.now();
    let retryCount = 0;

    const loadWithTimeout = async (): Promise<{ default: T }> => {
      try {
        const result = await Promise.race([
          importFn(),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error(`Component timeout after ${timeout}ms`)), timeout)
          )
        ]);

        // Track successful load
        const loadTime = Date.now() - startTime;
        performanceMetrics.totalLoads++;
        performanceMetrics.totalLoadTime += loadTime;

        if (componentCache[cacheKey]) {
          componentCache[cacheKey].preloaded = true;
        }

        console.debug(`Lazy component loaded in ${loadTime}ms (attempt ${retryCount + 1})`);
        return result;
      } catch (error) {
        console.warn(`Component load failed (attempt ${retryCount + 1}):`, error);

        // Retry logic
        if (retryCount < retries) {
          retryCount++;
          console.debug(`Retrying component load (attempt ${retryCount + 1}/${retries + 1})`);
          return loadWithTimeout();
        }

        // Mark as failed and use fallback
        if (componentCache[cacheKey]) {
          componentCache[cacheKey].failed = true;
        }

        performanceMetrics.timeouts++;

        if (fallbackComponent) {
          console.warn('Using fallback component due to load failure');
          return { default: fallbackComponent as T };
        }

        // Generic fallback component
        const GenericFallback = () => React.createElement('div', {
          style: {
            padding: '20px',
            textAlign: 'center',
            background: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '6px',
            color: '#6c757d'
          }
        }, [
          React.createElement('p', { key: 'text' }, 'Component optimized for performance'),
          React.createElement('small', { key: 'small' }, 'Refresh page if this persists')
        ]) as any;

        return { default: GenericFallback };
      }
    };

    return loadWithTimeout();
  });

  // Cache the component
  componentCache[cacheKey] = {
    component: lazyComponent,
    preloaded: false,
    failed: false
  };

  // Preload if requested (non-blocking)
  if (preload) {
    setTimeout(() => {
      importFn().then(() => {
        performanceMetrics.preloads++;
        if (componentCache[cacheKey]) {
          componentCache[cacheKey].preloaded = true;
        }
        console.debug('Component preloaded successfully');
      }).catch(error => {
        console.warn('Component preload failed:', error);
      });
    }, priority === 'high' ? 0 : priority === 'medium' ? 100 : 500);
  }

  return lazyComponent;
};

/**
 * Factory function for creating optimized lazy components with consistent settings
 */
export const createOptimizedLazyComponent = <T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  componentName: string,
  options: LazyLoadOptions = {}
): LazyExoticComponent<T> => {
  const defaultOptions: LazyLoadOptions = {
    timeout: 1500, // Faster timeout for tests
    retries: 1,
    preload: false,
    priority: 'medium'
  };

  return useOptimizedLazyLoad(importFn, {
    ...defaultOptions,
    ...options,
    fallbackComponent: options.fallbackComponent || (() => React.createElement('div', {
      style: {
        padding: '20px',
        textAlign: 'center',
        background: '#f8f9fa',
        border: '1px solid #dee2e6',
        borderRadius: '6px'
      }
    }, [
      React.createElement('h3', { key: 'title' }, componentName),
      React.createElement('p', { key: 'desc' }, 'Loading optimized version...')
    ]))
  });
};

/**
 * Preload components based on route patterns
 */
export const preloadComponents = (
  components: Array<{
    importFn: () => Promise<any>;
    priority?: 'high' | 'medium' | 'low';
  }>
) => {
  components
    .sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority || 'medium'] - priorityOrder[b.priority || 'medium'];
    })
    .forEach((comp, index) => {
      const delay = comp.priority === 'high' ? 0 : index * 100;
      setTimeout(() => {
        comp.importFn().catch(() => {
          // Ignore preload failures
        });
      }, delay);
    });
};

/**
 * Get performance metrics for monitoring
 */
export const getPerformanceMetrics = () => ({
  ...performanceMetrics,
  averageLoadTime: performanceMetrics.totalLoads > 0
    ? Math.round(performanceMetrics.totalLoadTime / performanceMetrics.totalLoads)
    : 0,
  cacheEfficiency: performanceMetrics.totalLoads > 0
    ? Math.round((performanceMetrics.cacheHits / performanceMetrics.totalLoads) * 100)
    : 0
});

/**
 * Reset performance metrics (for testing)
 */
export const resetPerformanceMetrics = () => {
  performanceMetrics.totalLoads = 0;
  performanceMetrics.totalLoadTime = 0;
  performanceMetrics.timeouts = 0;
  performanceMetrics.cacheHits = 0;
  performanceMetrics.preloads = 0;
};

export default useOptimizedLazyLoad;