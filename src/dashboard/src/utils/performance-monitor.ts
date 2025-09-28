/**
 * Performance Monitor for Terminal 2
 * 
 * Monitors frontend performance metrics, component render times, API latency,
 * WebSocket performance, and system resource usage
 * 
 * @fileoverview Production-ready performance monitoring for Dashboard
 * @version 1.0.0
 */

import * as React from 'react';
import { terminalSync } from '../services/terminal-sync';

// ================================
// TYPE DEFINITIONS
// ================================

export interface PerformanceMetrics {
  pageLoad: number;
  firstPaint: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  timeToInteractive: number;
  cumulativeLayoutShift: number;
  totalBlockingTime: number;
}

export interface ComponentMetric {
  id: string;
  phase: 'mount' | 'update' | 'unmount';
  duration: number;
  timestamp: number;
  interactions: number;
}

export interface ApiMetric {
  url: string;
  method: string;
  duration: number;
  status: number;
  size?: number;
  cached?: boolean;
  timestamp: number;
}

export interface WebSocketMetric {
  event: 'connect' | 'disconnect' | 'message_sent' | 'message_received' | 'ping';
  latency?: number;
  payload_size?: number;
  timestamp: number;
  success: boolean;
}

export interface SystemMetric {
  memory_usage: number; // MB
  cpu_usage: number; // Percentage
  heap_size: number; // MB
  dom_nodes: number;
  event_listeners: number;
  timestamp: number;
}

export interface PerformanceAlert {
  type: 'slow_component' | 'slow_api' | 'high_memory' | 'high_cpu' | 'high_latency' | 'layout_shift';
  severity: 'warning' | 'error' | 'critical';
  message: string;
  details: any;
  timestamp: string;
  suggestion?: string;
}

export interface PerformanceSummary {
  score: number; // 0-100
  metrics: PerformanceMetrics;
  topSlowComponents: ComponentMetric[];
  topSlowAPIs: ApiMetric[];
  systemHealth: SystemMetric;
  alerts: PerformanceAlert[];
  recommendations: string[];
}

// ================================
// PERFORMANCE MONITOR
// ================================

export class PerformanceMonitor {
  private static instance: PerformanceMonitor | null = null;
  private metrics: PerformanceMetrics;
  private componentMetrics: Map<string, ComponentMetric[]> = new Map();
  private apiMetrics: Map<string, ApiMetric[]> = new Map();
  private webSocketMetrics: WebSocketMetric[] = [];
  private systemMetrics: SystemMetric[] = [];
  private alerts: PerformanceAlert[] = [];
  private isMonitoring: boolean = false;
  private monitoringTimer: number | null = null;
  private observers: Map<string, PerformanceObserver> = new Map();

  // Thresholds for performance alerts
  private readonly thresholds = {
    componentRenderTime: 100, // ms
    apiCallDuration: 1000, // ms
    webSocketLatency: 500, // ms
    memoryUsage: 100, // MB
    cpuUsage: 80, // %
    layoutShift: 0.1, // CLS score
    totalBlockingTime: 300 // ms
  };

  constructor() {
    this.metrics = {
      pageLoad: 0,
      firstPaint: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      timeToInteractive: 0,
      cumulativeLayoutShift: 0,
      totalBlockingTime: 0
    };
  }

  // ================================
  // SINGLETON PATTERN
  // ================================

  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  // ================================
  // INITIALIZATION
  // ================================

  public startMonitoring(): void {
    if (this.isMonitoring) {
      console.warn('⚠️ Performance monitoring is already running');
      return;
    }

    console.log('📊 Starting performance monitoring');
    this.isMonitoring = true;

    // Initialize all monitoring systems
    this.initializeBasicMetrics();
    this.initializePerformanceObservers();
    this.monitorComponentPerformance();
    this.interceptAPIRequests();
    this.monitorWebSocketPerformance();
    this.monitorSystemResources();
    
    // Start periodic reporting
    this.startPeriodicReporting();

    console.log('✅ Performance monitoring started');
  }

  public stopMonitoring(): void {
    if (!this.isMonitoring) return;

    console.log('🛑 Stopping performance monitoring');
    this.isMonitoring = false;

    // Clear timers
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
      this.monitoringTimer = null;
    }

    // Disconnect observers
    this.observers.forEach((observer) => {
      observer.disconnect();
    });
    this.observers.clear();

    // Restore original functions
    this.restoreOriginalFetch();

    console.log('✅ Performance monitoring stopped');
  }

  // ================================
  // BASIC METRICS INITIALIZATION
  // ================================

  private initializeBasicMetrics(): void {
    if (typeof window === 'undefined' || !window.performance) {
      console.warn('⚠️ Performance API not available');
      return;
    }

    try {
      // Navigation timing
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navigation) {
        this.metrics.pageLoad = navigation.loadEventEnd - navigation.fetchStart;
      }

      // Paint timing
      const paintEntries = performance.getEntriesByType('paint');
      paintEntries.forEach((entry) => {
        if (entry.name === 'first-paint') {
          this.metrics.firstPaint = entry.startTime;
        } else if (entry.name === 'first-contentful-paint') {
          this.metrics.firstContentfulPaint = entry.startTime;
        }
      });

      // Long task timing for Total Blocking Time
      this.calculateTotalBlockingTime();

    } catch (error) {
      console.error('❌ Failed to initialize basic metrics:', error);
    }
  }

  private calculateTotalBlockingTime(): void {
    try {
      const longTaskEntries = performance.getEntriesByType('longtask') as any[];
      let totalBlockingTime = 0;

      longTaskEntries.forEach((entry) => {
        // Only count blocking time over 50ms
        if (entry.duration > 50) {
          totalBlockingTime += entry.duration - 50;
        }
      });

      this.metrics.totalBlockingTime = totalBlockingTime;

      if (totalBlockingTime > this.thresholds.totalBlockingTime) {
        this.addAlert({
          type: 'slow_component',
          severity: 'warning',
          message: `High Total Blocking Time: ${totalBlockingTime.toFixed(2)}ms`,
          details: { totalBlockingTime, threshold: this.thresholds.totalBlockingTime },
          timestamp: new Date().toISOString(),
          suggestion: 'Consider code-splitting or optimizing JavaScript execution'
        });
      }
    } catch (error) {
      console.warn('⚠️ Long task timing not supported:', error);
    }
  }

  // ================================
  // PERFORMANCE OBSERVERS
  // ================================
  
  private initializePerformanceObservers(): void {
    // Largest Contentful Paint
    try {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        this.metrics.largestContentfulPaint = lastEntry.renderTime || lastEntry.loadTime;
        
        // Alert if LCP is poor
        if (this.metrics.largestContentfulPaint > 2500) {
          this.addAlert({
            type: 'slow_component',
            severity: 'error',
            message: `Poor LCP: ${this.metrics.largestContentfulPaint.toFixed(2)}ms`,
            details: { lcp: this.metrics.largestContentfulPaint },
            timestamp: new Date().toISOString(),
            suggestion: 'Optimize images, preload critical resources, or use a CDN'
          });
        }
      });
      
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.set('lcp', lcpObserver);

    } catch (error) {
      console.warn('⚠️ LCP observer not supported:', error);
    }

    // Cumulative Layout Shift
    try {
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        
        this.metrics.cumulativeLayoutShift = clsValue;
        
        if (clsValue > this.thresholds.layoutShift) {
          this.addAlert({
            type: 'layout_shift',
            severity: 'warning',
            message: `High Cumulative Layout Shift: ${clsValue.toFixed(3)}`,
            details: { cls: clsValue, threshold: this.thresholds.layoutShift },
            timestamp: new Date().toISOString(),
            suggestion: 'Add size attributes to images and avoid inserting content above existing content'
          });
        }
      });
      
      clsObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.set('cls', clsObserver);

    } catch (error) {
      console.warn('⚠️ CLS observer not supported:', error);
    }

    // First Input Delay / Time to Interactive estimation
    try {
      const fidObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const fid = (entry as any).processingStart - entry.startTime;
          // Use FID as approximation for TTI
          this.metrics.timeToInteractive = entry.startTime + fid;
          
          if (fid > 100) {
            this.addAlert({
              type: 'slow_component',
              severity: 'warning',
              message: `High First Input Delay: ${fid.toFixed(2)}ms`,
              details: { fid, tti: this.metrics.timeToInteractive },
              timestamp: new Date().toISOString(),
              suggestion: 'Reduce JavaScript execution time or use web workers'
            });
          }
        }
      });
      
      fidObserver.observe({ entryTypes: ['first-input'] });
      this.observers.set('fid', fidObserver);

    } catch (error) {
      console.warn('⚠️ FID observer not supported:', error);
    }
  }

  // ================================
  // COMPONENT PERFORMANCE MONITORING
  // ================================

  private monitorComponentPerformance(): void {
    if (typeof window === 'undefined') return;

    // React Profiler integration
    this.integrateWithReactProfiler();
    
    // Generic component monitoring via mutation observer
    this.monitorDOMChanges();
    
    // Hook into React DevTools if available
    this.hookIntoReactDevTools();
  }

  private integrateWithReactProfiler(): void {
    // This would typically be done at the React component level
    // For now, we'll create a synthetic monitoring system
    
    if (typeof React !== 'undefined' && React.createElement && typeof window !== 'undefined') {
      try {
        const originalCreateElement = React.createElement;
        // Use Object.defineProperty to override the readonly property
        Object.defineProperty(React, 'createElement', {
          value: (type: any, props?: any, ...children: any[]) => {
            const startTime = performance.now();
            const result = originalCreateElement(type, props, ...children);
            const duration = performance.now() - startTime;
            
            if (duration > 0.1 && type && typeof type === 'function') {
              const componentName = type.name || type.displayName || 'Unknown';
              this.recordComponentMetric(componentName, 'mount', duration);
            }
            
            return result;
          },
          writable: true,
          configurable: true
        });
      } catch (error) {
        console.warn('⚠️ Could not patch React.createElement for performance monitoring:', error);
      }
    }
  }

  private monitorDOMChanges(): void {
    if (typeof MutationObserver === 'undefined') return;

    const observer = new MutationObserver((mutations) => {
      const startTime = performance.now();
      
      mutations.forEach((mutation) => {
        if (mutation.addedNodes.length > 0) {
          const endTime = performance.now();
          const duration = endTime - startTime;
          
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node as Element;
              const componentName = element.getAttribute('data-component') || 
                                  element.className || 
                                  element.tagName.toLowerCase();
              
              if (duration > 1) { // Only record significant render times
                this.recordComponentMetric(componentName, 'mount', duration);
              }
            }
          });
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: false
    });
  }

  private hookIntoReactDevTools(): void {
    // This would integrate with React DevTools if available
    if (typeof window !== 'undefined' && (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__) {
      const hook = (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__;
      
      hook.onCommitFiberRoot = (_id: any, _root: any, _priorityLevel: any) => {
        const duration = performance.now();
        this.recordComponentMetric('ReactRoot', 'update', duration);
      };
    }
  }

  private recordComponentMetric(componentId: string, phase: ComponentMetric['phase'], duration: number): void {
    const metric: ComponentMetric = {
      id: componentId,
      phase,
      duration,
      timestamp: Date.now(),
      interactions: 0 // Could be enhanced to track user interactions
    };

    const existing = this.componentMetrics.get(componentId) || [];
    existing.push(metric);
    
    // Keep only last 20 measurements per component
    if (existing.length > 20) {
      existing.shift();
    }
    
    this.componentMetrics.set(componentId, existing);

    // Alert for slow components
    if (duration > this.thresholds.componentRenderTime) {
      this.addAlert({
        type: 'slow_component',
        severity: duration > 200 ? 'error' : 'warning',
        message: `Slow component render: ${componentId} took ${duration.toFixed(2)}ms`,
        details: { componentId, phase, duration, threshold: this.thresholds.componentRenderTime },
        timestamp: new Date().toISOString(),
        suggestion: 'Consider memoization, virtualization, or code-splitting for this component'
      });
    }
  }

  // ================================
  // API PERFORMANCE MONITORING
  // ================================

  private originalFetch: typeof fetch | null = null;

  private interceptAPIRequests(): void {
    if (typeof window === 'undefined' || !window.fetch) return;

    this.originalFetch = window.fetch;
    
    window.fetch = async (...args: Parameters<typeof fetch>): Promise<Response> => {
      const startTime = performance.now();
      const url = args[0].toString();
      const method = (args[1]?.method || 'GET').toUpperCase();
      
      try {
        const response = await this.originalFetch!(...args);
        const duration = performance.now() - startTime;
        
        // Get response size if available
        const contentLength = response.headers.get('content-length');
        const size = contentLength ? parseInt(contentLength, 10) : undefined;
        
        // Check if response was cached
        const cached = response.headers.get('cache-control') !== null;
        
        const metric: ApiMetric = {
          url,
          method,
          duration,
          status: response.status,
          size,
          cached,
          timestamp: Date.now()
        };

        this.recordApiMetric(metric);
        
        // Alert for slow APIs
        if (duration > this.thresholds.apiCallDuration) {
          this.addAlert({
            type: 'slow_api',
            severity: duration > 3000 ? 'error' : 'warning',
            message: `Slow API call: ${method} ${url} took ${duration.toFixed(2)}ms`,
            details: { ...metric, threshold: this.thresholds.apiCallDuration },
            timestamp: new Date().toISOString(),
            suggestion: 'Consider caching, optimizing the API, or showing loading states'
          });
        }
        
        return response;
        
      } catch (error) {
        const duration = performance.now() - startTime;
        
        const metric: ApiMetric = {
          url,
          method,
          duration,
          status: 0,
          timestamp: Date.now()
        };

        this.recordApiMetric(metric);
        
        this.addAlert({
          type: 'slow_api',
          severity: 'error',
          message: `API call failed: ${method} ${url}`,
          details: { ...metric, error: error },
          timestamp: new Date().toISOString(),
          suggestion: 'Check network connectivity and API endpoint availability'
        });
        
        throw error;
      }
    };
  }

  private recordApiMetric(metric: ApiMetric): void {
    const key = `${metric.method} ${metric.url}`;
    const existing = this.apiMetrics.get(key) || [];
    existing.push(metric);
    
    // Keep only last 50 measurements per API
    if (existing.length > 50) {
      existing.shift();
    }
    
    this.apiMetrics.set(key, existing);
  }

  private restoreOriginalFetch(): void {
    if (this.originalFetch && typeof window !== 'undefined') {
      window.fetch = this.originalFetch;
      this.originalFetch = null;
    }
  }

  // ================================
  // WEBSOCKET PERFORMANCE MONITORING
  // ================================

  private monitorWebSocketPerformance(): void {
    // Monitor terminal sync WebSocket performance
    if (terminalSync) {
      terminalSync.on('terminal1:connected', () => {
        this.recordWebSocketMetric({
          event: 'connect',
          timestamp: Date.now(),
          success: true
        });
      });

      terminalSync.on('terminal1:disconnected', () => {
        this.recordWebSocketMetric({
          event: 'disconnect',
          timestamp: Date.now(),
          success: false
        });
      });

      // Monitor message latency
      this.startWebSocketLatencyMonitoring();
    }
  }

  private startWebSocketLatencyMonitoring(): void {
    setInterval(() => {
      if (terminalSync?.isTerminalConnected('terminal1')) {
        const startTime = Date.now();
        
        terminalSync.sendToTerminal('terminal1', {
          to: 'terminal1',
          type: 'ping',
          payload: { timestamp: startTime },
          priority: 'low'
        });

        // Listen for pong response
        const pongHandler = (data: any) => {
          const latency = Date.now() - data.timestamp;
          
          this.recordWebSocketMetric({
            event: 'ping',
            latency,
            timestamp: Date.now(),
            success: true
          });

          if (latency > this.thresholds.webSocketLatency) {
            this.addAlert({
              type: 'high_latency',
              severity: latency > 1000 ? 'error' : 'warning',
              message: `High WebSocket latency: ${latency}ms`,
              details: { latency, threshold: this.thresholds.webSocketLatency },
              timestamp: new Date().toISOString(),
              suggestion: 'Check network connectivity or consider connection pooling'
            });
          }
          
          terminalSync.off('message:pong', pongHandler);
        };

        terminalSync.on('message:pong', pongHandler);
        
        // Timeout if no response
        setTimeout(() => {
          terminalSync.off('message:pong', pongHandler);
        }, 5000);
      }
    }, 30000); // Every 30 seconds
  }

  private recordWebSocketMetric(metric: WebSocketMetric): void {
    this.webSocketMetrics.push(metric);
    
    // Keep only last 100 WebSocket metrics
    if (this.webSocketMetrics.length > 100) {
      this.webSocketMetrics.shift();
    }
  }

  // ================================
  // SYSTEM RESOURCE MONITORING
  // ================================

  private monitorSystemResources(): void {
    setInterval(() => {
      const metric: SystemMetric = {
        memory_usage: this.getMemoryUsage(),
        cpu_usage: this.getCPUUsage(),
        heap_size: this.getHeapSize(),
        dom_nodes: this.getDOMNodeCount(),
        event_listeners: this.getEventListenerCount(),
        timestamp: Date.now()
      };

      this.systemMetrics.push(metric);
      
      // Keep only last 60 measurements (30 minutes at 30s intervals)
      if (this.systemMetrics.length > 60) {
        this.systemMetrics.shift();
      }

      // Check for resource alerts
      this.checkResourceAlerts(metric);
      
    }, 30000); // Every 30 seconds
  }

  private getMemoryUsage(): number {
    if (typeof performance !== 'undefined' && 'memory' in performance) {
      const memory = (performance as any).memory;
      return Math.round(memory.usedJSHeapSize / 1024 / 1024); // Convert to MB
    }
    return 0;
  }

  private getCPUUsage(): number {
    // Simplified CPU usage estimation based on task timing
    const recentTasks = performance.getEntriesByType('measure').filter(
      entry => Date.now() - entry.startTime < 30000
    );
    
    if (recentTasks.length === 0) return 0;
    
    const avgDuration = recentTasks.reduce((sum, entry) => sum + entry.duration, 0) / recentTasks.length;
    return Math.min(Math.round(avgDuration / 10), 100); // Normalize to 0-100%
  }

  private getHeapSize(): number {
    if (typeof performance !== 'undefined' && 'memory' in performance) {
      const memory = (performance as any).memory;
      return Math.round(memory.totalJSHeapSize / 1024 / 1024); // Convert to MB
    }
    return 0;
  }

  private getDOMNodeCount(): number {
    if (typeof document !== 'undefined') {
      return document.getElementsByTagName('*').length;
    }
    return 0;
  }

  private getEventListenerCount(): number {
    // This is an approximation - real implementation would need custom tracking
    if (typeof document !== 'undefined') {
      const elements = document.querySelectorAll('*');
      let count = 0;
      
      // Check common event types
      const eventTypes = ['click', 'mouseover', 'keydown', 'scroll', 'resize'];
      
      elements.forEach(element => {
        eventTypes.forEach(eventType => {
          if ((element as any)[`on${eventType}`] !== null) {
            count++;
          }
        });
      });
      
      return count;
    }
    return 0;
  }

  private checkResourceAlerts(metric: SystemMetric): void {
    // Memory usage alert
    if (metric.memory_usage > this.thresholds.memoryUsage) {
      this.addAlert({
        type: 'high_memory',
        severity: metric.memory_usage > 150 ? 'critical' : 'warning',
        message: `High memory usage: ${metric.memory_usage}MB`,
        details: { ...metric, threshold: this.thresholds.memoryUsage },
        timestamp: new Date().toISOString(),
        suggestion: 'Check for memory leaks, reduce large data structures, or implement pagination'
      });
    }

    // CPU usage alert
    if (metric.cpu_usage > this.thresholds.cpuUsage) {
      this.addAlert({
        type: 'high_cpu',
        severity: metric.cpu_usage > 95 ? 'critical' : 'warning',
        message: `High CPU usage: ${metric.cpu_usage}%`,
        details: { ...metric, threshold: this.thresholds.cpuUsage },
        timestamp: new Date().toISOString(),
        suggestion: 'Optimize heavy computations, use web workers, or implement throttling'
      });
    }

    // DOM node count alert
    if (metric.dom_nodes > 5000) {
      this.addAlert({
        type: 'high_memory',
        severity: 'warning',
        message: `High DOM node count: ${metric.dom_nodes}`,
        details: { dom_nodes: metric.dom_nodes },
        timestamp: new Date().toISOString(),
        suggestion: 'Consider virtualization for large lists or reduce DOM complexity'
      });
    }
  }

  // ================================
  // PERIODIC REPORTING
  // ================================

  private startPeriodicReporting(): void {
    this.monitoringTimer = setInterval(() => {
      this.sendPerformanceReport();
    }, 60000); // Every minute
  }

  private sendPerformanceReport(): void {
    if (!this.isMonitoring || !terminalSync) return;

    const summary = this.getPerformanceSummary();
    
    terminalSync.sendToTerminal('debugger', {
      to: 'debugger',
      type: 'frontend_metrics',
      payload: {
        terminal: 'terminal2',
        performance_summary: summary,
        timestamp: new Date().toISOString()
      },
      priority: 'normal'
    }).catch(error => {
      console.warn('⚠️ Failed to send performance report:', error);
    });

    // Also send to Terminal 1 for general monitoring
    terminalSync.sendToTerminal('terminal1', {
      to: 'terminal1',
      type: 'performance_update',
      payload: {
        score: summary.score,
        critical_alerts: summary.alerts.filter(a => a.severity === 'critical').length,
        memory_usage: summary.systemHealth.memory_usage,
        avg_api_latency: this.calculateAverageApiLatency()
      },
      priority: 'low'
    }).catch(error => {
      console.warn('⚠️ Failed to send performance update:', error);
    });
  }

  // ================================
  // ALERT MANAGEMENT
  // ================================

  private addAlert(alert: PerformanceAlert): void {
    this.alerts.push(alert);
    
    // Keep only last 50 alerts
    if (this.alerts.length > 50) {
      this.alerts.shift();
    }

    // Log alert to console
    const logMethod = alert.severity === 'critical' ? 'error' : 
                     alert.severity === 'error' ? 'error' : 'warn';
    console[logMethod](`🚨 Performance Alert [${alert.severity.toUpperCase()}]:`, alert.message);

    // Emit alert event
    if (terminalSync) {
      terminalSync.emit('performance_alert', alert);
    }
  }

  // ================================
  // UTILITY METHODS
  // ================================

  private calculatePerformanceScore(): number {
    // Simplified performance score calculation (0-100)
    let score = 100;
    
    // Deduct points based on metrics
    if (this.metrics.largestContentfulPaint > 2500) score -= 20;
    if (this.metrics.firstContentfulPaint > 1800) score -= 15;
    if (this.metrics.cumulativeLayoutShift > 0.1) score -= 15;
    if (this.metrics.totalBlockingTime > 300) score -= 20;
    
    // Deduct points for recent alerts
    const recentAlerts = this.alerts.filter(
      alert => Date.now() - new Date(alert.timestamp).getTime() < 300000 // Last 5 minutes
    );
    
    recentAlerts.forEach(alert => {
      switch (alert.severity) {
        case 'critical': score -= 10; break;
        case 'error': score -= 5; break;
        case 'warning': score -= 2; break;
      }
    });
    
    return Math.max(0, Math.min(100, score));
  }

  private calculateAverageApiLatency(): number {
    const allApiMetrics = Array.from(this.apiMetrics.values()).flat();
    if (allApiMetrics.length === 0) return 0;
    
    const totalLatency = allApiMetrics.reduce((sum, metric) => sum + metric.duration, 0);
    return Math.round(totalLatency / allApiMetrics.length);
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];
    
    if (this.metrics.largestContentfulPaint > 2500) {
      recommendations.push('Optimize images and use lazy loading to improve LCP');
    }
    
    if (this.metrics.cumulativeLayoutShift > 0.1) {
      recommendations.push('Add explicit dimensions to images and avoid inserting content dynamically');
    }
    
    const slowComponents = this.getTopSlowComponents(5);
    if (slowComponents.length > 0) {
      recommendations.push(`Optimize slow components: ${slowComponents.map(c => c.id).join(', ')}`);
    }
    
    const recentMemoryAlerts = this.alerts.filter(
      alert => alert.type === 'high_memory' && 
               Date.now() - new Date(alert.timestamp).getTime() < 600000
    );
    
    if (recentMemoryAlerts.length > 0) {
      recommendations.push('Implement memory optimization strategies or check for memory leaks');
    }
    
    return recommendations;
  }

  // ================================
  // PUBLIC API
  // ================================

  public getPerformanceSummary(): PerformanceSummary {
    const currentSystemMetric = this.systemMetrics[this.systemMetrics.length - 1] || {
      memory_usage: 0,
      cpu_usage: 0,
      heap_size: 0,
      dom_nodes: 0,
      event_listeners: 0,
      timestamp: Date.now()
    };

    return {
      score: this.calculatePerformanceScore(),
      metrics: { ...this.metrics },
      topSlowComponents: this.getTopSlowComponents(10),
      topSlowAPIs: this.getTopSlowAPIs(10),
      systemHealth: currentSystemMetric,
      alerts: [...this.alerts].slice(-20), // Last 20 alerts
      recommendations: this.generateRecommendations()
    };
  }

  public getTopSlowComponents(limit: number = 10): ComponentMetric[] {
    const allComponents = Array.from(this.componentMetrics.values()).flat();
    return allComponents
      .sort((a, b) => b.duration - a.duration)
      .slice(0, limit);
  }

  public getTopSlowAPIs(limit: number = 10): ApiMetric[] {
    const allAPIs = Array.from(this.apiMetrics.values()).flat();
    return allAPIs
      .sort((a, b) => b.duration - a.duration)
      .slice(0, limit);
  }

  public getRecentAlerts(minutes: number = 30): PerformanceAlert[] {
    const cutoff = Date.now() - (minutes * 60 * 1000);
    return this.alerts.filter(alert => 
      new Date(alert.timestamp).getTime() > cutoff
    );
  }

  public clearAlerts(): void {
    this.alerts = [];
    console.log('🧹 Performance alerts cleared');
  }

  public updateThresholds(newThresholds: Partial<typeof this.thresholds>): void {
    Object.assign(this.thresholds, newThresholds);
    console.log('⚙️ Performance thresholds updated:', this.thresholds);
  }

  public isRunning(): boolean {
    return this.isMonitoring;
  }
}

// ================================
// EXPORT SINGLETON
// ================================

export default PerformanceMonitor;

// Create and export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

// Global exposure for debugging
if (typeof window !== 'undefined') {
  (window as any).__PERFORMANCE_MONITOR__ = performanceMonitor;
  
  // Auto-start monitoring in development mode
  if (import.meta.env.DEV) {
    console.log('🚀 Performance monitor created');
    
    // Start monitoring after app initialization
    setTimeout(() => {
      performanceMonitor.startMonitoring();
    }, 3000);
  }
}