/**
 * Performance Monitoring Utilities for ToolBoxAI Dashboard
 *
 * Provides comprehensive performance tracking, monitoring, and reporting
 * capabilities for the application.
 */

// Google Analytics gtag function type
type GtagFunction = (...args: any[]) => void;
declare const gtag: GtagFunction | undefined;

interface PerformanceMetric {
  name: string;
  value: number;
  rating?: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

interface WebVitalsConfig {
  enableLogging?: boolean;
  enableAnalytics?: boolean;
  analyticsEndpoint?: string;
  sampleRate?: number;
}

// Performance thresholds based on Web Vitals standards
const PERFORMANCE_THRESHOLDS = {
  // Largest Contentful Paint (LCP)
  LCP: {
    good: 2500,
    poor: 4000
  },
  // First Input Delay (FID)
  FID: {
    good: 100,
    poor: 300
  },
  // Cumulative Layout Shift (CLS)
  CLS: {
    good: 0.1,
    poor: 0.25
  },
  // First Contentful Paint (FCP)
  FCP: {
    good: 1800,
    poor: 3000
  },
  // Time to First Byte (TTFB)
  TTFB: {
    good: 800,
    poor: 1800
  },
  // Interaction to Next Paint (INP)
  INP: {
    good: 200,
    poor: 500
  }
};

/**
 * Performance monitor singleton class
 */
class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Map<string, PerformanceMetric[]> = new Map();
  private observers: Map<string, PerformanceObserver> = new Map();
  private config: WebVitalsConfig = {};
  private isInitialized = false;

  private constructor() {}

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Initialize performance monitoring
   */
  initialize(config: WebVitalsConfig = {}): void {
    if (this.isInitialized) {
      console.warn('Performance monitor already initialized');
      return;
    }

    this.config = {
      enableLogging: process.env.NODE_ENV === 'development',
      enableAnalytics: true,
      sampleRate: 1.0,
      ...config
    };

    // Check if Performance API is available
    if (typeof window === 'undefined' || !window.performance) {
      console.warn('Performance API not available');
      return;
    }

    this.setupObservers();
    this.trackNavigationTiming();
    this.trackResourceTiming();
    this.isInitialized = true;

    if (this.config.enableLogging) {
      console.log('Performance monitoring initialized', this.config);
    }
  }

  /**
   * Setup performance observers for various metrics
   */
  private setupObservers(): void {
    // Observe Largest Contentful Paint
    this.observeLCP();

    // Observe First Input Delay
    this.observeFID();

    // Observe Cumulative Layout Shift
    this.observeCLS();

    // Observe First Contentful Paint
    this.observeFCP();

    // Observe Interaction to Next Paint
    this.observeINP();

    // Observe Long Tasks
    this.observeLongTasks();
  }

  /**
   * Observe Largest Contentful Paint
   */
  private observeLCP(): void {
    if (!PerformanceObserver.supportedEntryTypes?.includes('largest-contentful-paint')) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const metric = this.createMetric('LCP', entry.startTime);
        this.recordMetric(metric);
      }
    });

    observer.observe({ type: 'largest-contentful-paint', buffered: true });
    this.observers.set('lcp', observer);
  }

  /**
   * Observe First Input Delay
   */
  private observeFID(): void {
    if (!PerformanceObserver.supportedEntryTypes?.includes('first-input')) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const fidEntry = entry as CustomPerformanceEventTiming;
        const metric = this.createMetric(
          'FID',
          fidEntry.processingStart - fidEntry.startTime
        );
        this.recordMetric(metric);
      }
    });

    observer.observe({ type: 'first-input', buffered: true });
    this.observers.set('fid', observer);
  }

  /**
   * Observe Cumulative Layout Shift
   */
  private observeCLS(): void {
    if (!PerformanceObserver.supportedEntryTypes?.includes('layout-shift')) {
      return;
    }

    let clsValue = 0;
    const clsEntries: PerformanceEntry[] = [];

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const layoutShift = entry as any;
        // Only count layout shifts without recent user input
        if (!layoutShift.hadRecentInput) {
          clsValue += layoutShift.value;
          clsEntries.push(entry);
        }
      }

      const metric = this.createMetric('CLS', clsValue);
      this.recordMetric(metric);
    });

    observer.observe({ type: 'layout-shift', buffered: true });
    this.observers.set('cls', observer);
  }

  /**
   * Observe First Contentful Paint
   */
  private observeFCP(): void {
    if (!PerformanceObserver.supportedEntryTypes?.includes('paint')) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          const metric = this.createMetric('FCP', entry.startTime);
          this.recordMetric(metric);
        }
      }
    });

    observer.observe({ type: 'paint', buffered: true });
    this.observers.set('fcp', observer);
  }

  /**
   * Observe Interaction to Next Paint
   */
  private observeINP(): void {
    if (!PerformanceObserver.supportedEntryTypes?.includes('event')) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const eventEntry = entry as CustomPerformanceEventTiming;
        const duration = eventEntry.duration;

        if (duration > 0) {
          const metric = this.createMetric('INP', duration);
          this.recordMetric(metric);
        }
      }
    });

    observer.observe({ type: 'event', buffered: true, durationThreshold: 40 });
    this.observers.set('inp', observer);
  }

  /**
   * Observe Long Tasks
   */
  private observeLongTasks(): void {
    if (!PerformanceObserver.supportedEntryTypes?.includes('longtask')) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.recordMetric({
          name: 'LongTask',
          value: entry.duration,
          timestamp: Date.now()
        });

        if (this.config.enableLogging) {
          console.warn(`Long task detected: ${entry.duration}ms`);
        }
      }
    });

    observer.observe({ type: 'longtask' });
    this.observers.set('longtask', observer);
  }

  /**
   * Track navigation timing metrics
   */
  private trackNavigationTiming(): void {
    if (!window.performance?.timing) {
      return;
    }

    const timing = window.performance.timing;
    const navigationStart = timing.navigationStart;

    // Time to First Byte
    const ttfb = timing.responseStart - navigationStart;
    this.recordMetric(this.createMetric('TTFB', ttfb));

    // DOM Content Loaded
    const dcl = timing.domContentLoadedEventEnd - navigationStart;
    this.recordMetric({
      name: 'DCL',
      value: dcl,
      timestamp: Date.now()
    });

    // Page Load Time
    const loadTime = timing.loadEventEnd - navigationStart;
    this.recordMetric({
      name: 'PageLoad',
      value: loadTime,
      timestamp: Date.now()
    });
  }

  /**
   * Track resource timing metrics
   */
  private trackResourceTiming(): void {
    if (!window.performance?.getEntriesByType) {
      return;
    }

    const resources = window.performance.getEntriesByType('resource');
    const resourceMetrics = {
      scripts: [] as number[],
      stylesheets: [] as number[],
      images: [] as number[],
      fonts: [] as number[],
      xhr: [] as number[]
    };

    resources.forEach((resource: any) => {
      const duration = resource.responseEnd - resource.startTime;

      if (resource.initiatorType === 'script') {
        resourceMetrics.scripts.push(duration);
      } else if (resource.initiatorType === 'css') {
        resourceMetrics.stylesheets.push(duration);
      } else if (resource.initiatorType === 'img') {
        resourceMetrics.images.push(duration);
      } else if (resource.initiatorType === 'font') {
        resourceMetrics.fonts.push(duration);
      } else if (resource.initiatorType === 'xmlhttprequest' || resource.initiatorType === 'fetch') {
        resourceMetrics.xhr.push(duration);
      }
    });

    // Record aggregated metrics
    Object.entries(resourceMetrics).forEach(([type, durations]) => {
      if (durations.length > 0) {
        const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
        const max = Math.max(...durations);

        this.recordMetric({
          name: `Resource_${type}_avg`,
          value: avg,
          timestamp: Date.now()
        });

        this.recordMetric({
          name: `Resource_${type}_max`,
          value: max,
          timestamp: Date.now()
        });
      }
    });
  }

  /**
   * Create a performance metric with rating
   */
  private createMetric(name: string, value: number): PerformanceMetric {
    const thresholds = PERFORMANCE_THRESHOLDS[name as keyof typeof PERFORMANCE_THRESHOLDS];
    let rating: 'good' | 'needs-improvement' | 'poor' | undefined;

    if (thresholds) {
      if (value <= thresholds.good) {
        rating = 'good';
      } else if (value <= thresholds.poor) {
        rating = 'needs-improvement';
      } else {
        rating = 'poor';
      }
    }

    return {
      name,
      value,
      rating,
      timestamp: Date.now()
    };
  }

  /**
   * Record a performance metric
   */
  private recordMetric(metric: PerformanceMetric): void {
    // Store metric
    if (!this.metrics.has(metric.name)) {
      this.metrics.set(metric.name, []);
    }
    this.metrics.get(metric.name)!.push(metric);

    // Log if enabled
    if (this.config.enableLogging) {
      const ratingEmoji = metric.rating === 'good' ? '✅' :
                          metric.rating === 'needs-improvement' ? '⚠️' :
                          metric.rating === 'poor' ? '❌' : '📊';
      console.log(
        `${ratingEmoji} ${metric.name}: ${metric.value.toFixed(2)}ms`,
        metric.rating ? `(${metric.rating})` : ''
      );
    }

    // Send to analytics if enabled
    if (this.config.enableAnalytics && Math.random() < (this.config.sampleRate || 1)) {
      this.sendToAnalytics(metric);
    }
  }

  /**
   * Send metric to analytics service
   */
  private sendToAnalytics(metric: PerformanceMetric): void {
    // Google Analytics
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'web_vitals', {
        event_category: 'Performance',
        event_label: metric.name,
        value: Math.round(metric.value),
        metric_rating: metric.rating,
        non_interaction: true
      });
    }

    // Custom analytics endpoint
    if (this.config.analyticsEndpoint) {
      fetch(this.config.analyticsEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          metric,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: metric.timestamp
        }),
        keepalive: true
      }).catch(error => {
        console.error('Failed to send performance metric:', error);
      });
    }
  }

  /**
   * Mark a custom timing
   */
  mark(name: string): void {
    if (!window.performance?.mark) {
      return;
    }
    window.performance.mark(name);
  }

  /**
   * Measure between two marks
   */
  measure(name: string, startMark: string, endMark?: string): void {
    if (!window.performance?.measure) {
      return;
    }

    try {
      const measure = endMark
        ? window.performance.measure(name, startMark, endMark)
        : window.performance.measure(name, startMark);

      this.recordMetric({
        name: `Custom_${name}`,
        value: measure.duration,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('Failed to measure performance:', error);
    }
  }

  /**
   * Get all recorded metrics
   */
  getMetrics(): Map<string, PerformanceMetric[]> {
    return this.metrics;
  }

  /**
   * Get specific metric
   */
  getMetric(name: string): PerformanceMetric[] | undefined {
    return this.metrics.get(name);
  }

  /**
   * Get latest metric value
   */
  getLatestMetricValue(name: string): number | undefined {
    const metrics = this.metrics.get(name);
    if (!metrics || metrics.length === 0) {
      return undefined;
    }
    return metrics[metrics.length - 1].value;
  }

  /**
   * Get performance summary
   */
  getSummary(): Record<string, any> {
    const summary: Record<string, any> = {};

    this.metrics.forEach((metrics, name) => {
      if (metrics.length > 0) {
        const values = metrics.map(m => m.value);
        summary[name] = {
          count: metrics.length,
          min: Math.min(...values),
          max: Math.max(...values),
          avg: values.reduce((a, b) => a + b, 0) / values.length,
          latest: metrics[metrics.length - 1]
        };
      }
    });

    return summary;
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics.clear();
  }

  /**
   * Cleanup and disconnect observers
   */
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    this.clearMetrics();
    this.isInitialized = false;
  }
}

// Export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

/**
 * Report Web Vitals using the web-vitals library
 */
export const reportWebVitals = (onPerfEntry?: (metric: any) => void): void => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ onCLS, onFCP, onLCP, onTTFB, onINP }) => {
      onCLS(onPerfEntry);
      onFCP(onPerfEntry);
      onLCP(onPerfEntry);
      onTTFB(onPerfEntry);
      onINP(onPerfEntry);
    });
  }
};

/**
 * Track bundle size (called during build)
 */
export const trackBundleSize = async (): Promise<void> => {
  if (process.env.NODE_ENV !== 'production') {
    return;
  }

  try {
    // This would be populated by the build process
    const stats = await fetch('/.vite/manifest.json').then(r => r.json());

    const bundleInfo = {
      totalSize: 0,
      chunks: [] as any[]
    };

    Object.entries(stats).forEach(([file, info]: [string, any]) => {
      if (info.file && info.size) {
        bundleInfo.totalSize += info.size;
        bundleInfo.chunks.push({
          file: info.file,
          size: info.size,
          imports: info.imports || []
        });
      }
    });

    // Log bundle info
    console.log('Bundle Analysis:', bundleInfo);

    // Send to analytics
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'bundle_size', {
        event_category: 'Performance',
        value: Math.round(bundleInfo.totalSize / 1024), // KB
        non_interaction: true
      });
    }
  } catch (error) {
    console.error('Failed to track bundle size:', error);
  }
};

/**
 * Performance decorator for measuring function execution time
 */
export function measurePerformance(target: any, propertyKey: string, descriptor: PropertyDescriptor): void {
  const originalMethod = descriptor.value;

  descriptor.value = async function (...args: any[]) {
    const startTime = performance.now();
    const startMark = `${propertyKey}_start_${Date.now()}`;
    const endMark = `${propertyKey}_end_${Date.now()}`;

    performanceMonitor.mark(startMark);

    try {
      const result = await originalMethod.apply(this, args);

      performanceMonitor.mark(endMark);
      performanceMonitor.measure(propertyKey, startMark, endMark);

      const duration = performance.now() - startTime;
      if (duration > 100) {
        console.warn(`Slow function detected: ${propertyKey} took ${duration.toFixed(2)}ms`);
      }

      return result;
    } catch (error) {
      const duration = performance.now() - startTime;
      console.error(`Function ${propertyKey} failed after ${duration.toFixed(2)}ms`, error);
      throw error;
    }
  };
}

// Extend window interface for gtag
declare global {
  interface Window {
    gtag?: GtagFunction;
  }
}

// Custom performance event timing interface
interface CustomPerformanceEventTiming extends PerformanceEntry {
  processingStart: DOMHighResTimeStamp;
  processingEnd?: DOMHighResTimeStamp;
  duration: DOMHighResTimeStamp;
  cancelable?: boolean;
  target?: Node;
}

// Initialize performance monitoring on module load
if (typeof window !== 'undefined' && window.performance) {
  performanceMonitor.initialize();
}