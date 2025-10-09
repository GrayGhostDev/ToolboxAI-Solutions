/**
 * Performance Monitor Hook
 *
 * React hook for integrating performance monitoring with feature flags
 * Provides controlled access to performance monitoring based on configuration
 */
import { useEffect, useRef, useState } from 'react';
import { performanceMonitor, type PerformanceSummary } from '@/utils/performance-monitor';
import { useFeatureFlag } from '@/config/features';
export interface UsePerformanceMonitorOptions {
  // Override feature flag settings
  forceEnable?: boolean;
  forceDisable?: boolean;
  // Custom thresholds
  thresholds?: {
    componentRenderTime?: number;
    apiCallDuration?: number;
    webSocketLatency?: number;
    memoryUsage?: number;
    cpuUsage?: number;
  };
  // Reporting options
  onReport?: (summary: PerformanceSummary) => void;
  reportingInterval?: number;
}
export interface UsePerformanceMonitorResult {
  isMonitoring: boolean;
  summary: PerformanceSummary | null;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  clearAlerts: () => void;
  updateThresholds: (thresholds: any) => void;
}
/**
 * Hook for performance monitoring with feature flag control
 */
export function usePerformanceMonitor(
  options: UsePerformanceMonitorOptions = {}
): UsePerformanceMonitorResult {
  const {
    forceEnable = false,
    forceDisable = false,
    thresholds,
    onReport,
    reportingInterval,
  } = options;
  // Feature flags
  const enablePerformanceMonitoring = useFeatureFlag('enablePerformanceMonitoring');
  const performanceLevel = useFeatureFlag('performanceMonitoringLevel');
  const defaultReportingInterval = useFeatureFlag('performanceReportingInterval');
  // State
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [summary, setSummary] = useState<PerformanceSummary | null>(null);
  // Refs
  const reportingTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const isInitialized = useRef(false);
  /**
   * Determine if monitoring should be enabled
   */
  const shouldMonitor = (): boolean => {
    if (forceDisable) return false;
    if (forceEnable) return true;
    return enablePerformanceMonitoring && performanceLevel !== 'off';
  };
  /**
   * Start performance monitoring
   */
  const startMonitoring = (): void => {
    if (isMonitoring || !shouldMonitor()) return;
    console.log('🚀 Starting performance monitoring (feature-flag controlled)');
    // Update thresholds if provided
    if (thresholds) {
      performanceMonitor.updateThresholds(thresholds);
    }
    // Start monitoring
    performanceMonitor.startMonitoring();
    setIsMonitoring(true);
    // Setup reporting
    const interval = reportingInterval || defaultReportingInterval;
    if (interval > 0) {
      reportingTimer.current = setInterval(() => {
        const currentSummary = performanceMonitor.getPerformanceSummary();
        setSummary(currentSummary);
        // Call custom report handler if provided
        if (onReport) {
          onReport(currentSummary);
        }
        // Log summary based on performance level
        if (performanceLevel === 'verbose') {
          console.log('📊 Performance Report (Verbose):', currentSummary);
        } else if (performanceLevel === 'detailed') {
          console.log('📊 Performance Score:', currentSummary.score);
          console.log('⚠️ Active Alerts:', currentSummary.alerts.length);
        } else if (performanceLevel === 'basic') {
          console.log('📊 Performance Score:', currentSummary.score);
        }
      }, interval);
    }
  };
  /**
   * Stop performance monitoring
   */
  const stopMonitoring = (): void => {
    if (!isMonitoring) return;
    console.log('🛑 Stopping performance monitoring');
    // Clear reporting timer
    if (reportingTimer.current) {
      clearInterval(reportingTimer.current);
      reportingTimer.current = null;
    }
    // Stop monitoring
    performanceMonitor.stopMonitoring();
    setIsMonitoring(false);
    setSummary(null);
  };
  /**
   * Clear performance alerts
   */
  const clearAlerts = (): void => {
    performanceMonitor.clearAlerts();
    // Update summary to reflect cleared alerts
    if (isMonitoring) {
      setSummary(performanceMonitor.getPerformanceSummary());
    }
  };
  /**
   * Update performance thresholds
   */
  const updateThresholds = (newThresholds: any): void => {
    performanceMonitor.updateThresholds(newThresholds);
  };
  /**
   * Effect: Initialize monitoring based on feature flags
   */
  useEffect(() => {
    // Skip if already initialized or shouldn't monitor
    if (isInitialized.current) return;
    if (shouldMonitor()) {
      // Delay start to allow app to initialize
      const timer = setTimeout(() => {
        startMonitoring();
        isInitialized.current = true;
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [enablePerformanceMonitoring, performanceLevel]);
  /**
   * Effect: Handle feature flag changes
   */
  useEffect(() => {
    // If feature flag changed and we're initialized
    if (isInitialized.current) {
      if (shouldMonitor() && !isMonitoring) {
        startMonitoring();
      } else if (!shouldMonitor() && isMonitoring) {
        stopMonitoring();
      }
    }
  }, [enablePerformanceMonitoring, performanceLevel]);
  /**
   * Effect: Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (reportingTimer.current) {
        clearInterval(reportingTimer.current);
      }
    };
  }, []);
  return {
    isMonitoring,
    summary,
    startMonitoring,
    stopMonitoring,
    clearAlerts,
    updateThresholds,
  };
}
/**
 * Hook for tracking component performance
 */
export function useComponentPerformance(componentName: string) {
  const startTime = useRef<number>(0);
  const isMonitoring = useFeatureFlag('enablePerformanceMonitoring');
  const level = useFeatureFlag('performanceMonitoringLevel');
  useEffect(() => {
    if (!isMonitoring || level === 'off' || level === 'basic') return;
    // Record mount time
    startTime.current = performance.now();
    return () => {
      // Record unmount time
      const duration = performance.now() - startTime.current;
      if (duration > 0 && level === 'verbose') {
        console.log(`⚡ Component [${componentName}] lifecycle: ${duration.toFixed(2)}ms`);
      }
    };
  }, [componentName, isMonitoring, level]);
}
/**
 * Hook for tracking API performance
 */
export function useApiPerformance() {
  const enableSlowApiWarnings = useFeatureFlag('enableSlowApiWarnings');
  const apiTimeoutThreshold = useFeatureFlag('apiTimeoutThreshold');
  const trackApiCall = (url: string, startTime: number, endTime: number, status: number) => {
    if (!enableSlowApiWarnings) return;
    const duration = endTime - startTime;
    if (duration > apiTimeoutThreshold) {
      console.warn(`🐌 Slow API call detected: ${url} took ${duration.toFixed(2)}ms`);
    }
    // Could also send to analytics or monitoring service
  };
  return { trackApiCall };
}