import React, { useEffect, useState, useCallback } from 'react';
import { onCLS, onFCP, onFID, onLCP, onTTFB, Metric } from 'web-vitals';

export interface PerformanceMetrics {
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  ttfb?: number; // Time to First Byte
}

interface PerformanceMonitorProps {
  onMetric?: (metric: Metric) => void;
  enabled?: boolean;
}

/**
 * Performance monitoring component that tracks Web Vitals
 * Only active in development or when explicitly enabled
 */
export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  onMetric,
  enabled = process.env.NODE_ENV === 'development'
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});

  const handleMetric = useCallback((metric: Metric) => {
    setMetrics(prev => ({
      ...prev,
      [metric.name.toLowerCase()]: metric.value
    }));

    // Log performance metrics in development
    if (enabled) {
      console.group(`🚀 Web Vitals: ${metric.name}`);
      console.log('Value:', metric.value);
      console.log('Rating:', metric.rating);
      console.log('Delta:', metric.delta);
      console.groupEnd();
    }

    onMetric?.(metric);
  }, [onMetric, enabled]);

  useEffect(() => {
    if (!enabled) return;

    // Set up Web Vitals monitoring
    onFCP(handleMetric);
    onLCP(handleMetric);
    onFID(handleMetric);
    onCLS(handleMetric);
    onTTFB(handleMetric);

    // Add custom performance marks
    performance.mark('dashboard-mount');

    return () => {
      performance.clearMarks('dashboard-mount');
    };
  }, [handleMetric, enabled]);

  // Development performance display
  if (enabled && process.env.NODE_ENV === 'development') {
    return (
      <div
        style={{
          position: 'fixed',
          top: 10,
          right: 10,
          background: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '4px',
          fontSize: '12px',
          fontFamily: 'monospace',
          zIndex: 9999,
          maxWidth: '200px'
        }}
      >
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Web Vitals</div>
        {metrics.fcp && <div>FCP: {Math.round(metrics.fcp)}ms</div>}
        {metrics.lcp && <div>LCP: {Math.round(metrics.lcp)}ms</div>}
        {metrics.fid && <div>FID: {Math.round(metrics.fid)}ms</div>}
        {metrics.cls && <div>CLS: {metrics.cls.toFixed(3)}</div>}
        {metrics.ttfb && <div>TTFB: {Math.round(metrics.ttfb)}ms</div>}
      </div>
    );
  }

  return null;
};

/**
 * Hook for accessing performance metrics
 */
export const usePerformanceMetrics = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});

  useEffect(() => {
    const handleMetric = (metric: Metric) => {
      setMetrics(prev => ({
        ...prev,
        [metric.name.toLowerCase()]: metric.value
      }));
    };

    onFCP(handleMetric);
    onLCP(handleMetric);
    onFID(handleMetric);
    onCLS(handleMetric);
    onTTFB(handleMetric);
  }, []);

  return metrics;
};

/**
 * Performance utilities for measuring custom metrics
 */
export const performanceUtils = {
  mark: (name: string) => {
    performance.mark(name);
  },

  measure: (name: string, startMark: string, endMark?: string) => {
    try {
      performance.measure(name, startMark, endMark);
      const measure = performance.getEntriesByName(name, 'measure')[0];
      return measure?.duration || 0;
    } catch (error) {
      console.warn('Performance measurement failed:', error);
      return 0;
    }
  },

  measureComponent: (componentName: string) => {
    const startMark = `${componentName}-start`;
    const endMark = `${componentName}-end`;

    return {
      start: () => performance.mark(startMark),
      end: () => {
        performance.mark(endMark);
        return performanceUtils.measure(`${componentName}-render`, startMark, endMark);
      }
    };
  }
};

export default PerformanceMonitor;