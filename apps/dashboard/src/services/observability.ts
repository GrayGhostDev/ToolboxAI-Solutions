/**
 * Observability service for fetching metrics and managing real-time connections.
 */

import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import { pusherService } from './pusher';

// Types for observability data
export interface Metric {
  timestamp: string;
  value: number;
  labels?: Record<string, string>;
}

export interface TimeSeriesData {
  name: string;
  data: Array<{ time: string; value: number }>;
}

export interface TraceSpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  operationName: string;
  serviceName: string;
  startTime: string;
  endTime: string;
  duration: number;
  tags: Record<string, any>;
  logs: Array<{ timestamp: string; message: string }>;
  status: 'ok' | 'error' | 'cancelled';
}

export interface Trace {
  traceId: string;
  rootSpan: TraceSpan;
  spans: TraceSpan[];
  totalDuration: number;
  services: string[];
  errorCount: number;
}

export interface Anomaly {
  id: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  description: string;
  metric: string;
  value: number;
  expectedRange: { min: number; max: number };
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
}

export interface ComponentHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'critical' | 'unknown';
  lastCheck: string;
  metrics: Record<string, any>;
  message?: string;
}

export interface SystemStatus {
  uptime: number;
  activeConnections: number;
  cacheHitRate: number;
  databasePoolUsage: number;
  rateLimitRemaining: number;
}

export interface MetricsResponse {
  status: string;
  data: {
    metrics: {
      latency: TimeSeriesData[];
      throughput: TimeSeriesData[];
      errorRate: TimeSeriesData[];
      saturation: TimeSeriesData[];
    };
    systemStatus: SystemStatus;
    timeRange: {
      start: string;
      end: string;
      resolution: number;
    };
  };
}

export interface ComponentHealthResponse {
  status: string;
  data: {
    components: {
      circuitBreakers: ComponentHealth;
      rateLimiters: ComponentHealth;
      databaseReplicas: ComponentHealth;
      edgeCache: ComponentHealth;
      websocketCluster: ComponentHealth;
    };
    healthScore: number;
    timestamp: string;
  };
}

// Pusher connection for real-time metrics
class MetricsPusherConnection {
  private subscriptionId: string | null = null;
  private listeners: Set<(data: any) => void> = new Set();
  private isActive: boolean = false;

  async connect() {
    if (this.isActive) {
      return;
    }

    try {
      // Ensure pusher service is connected
      if (!pusherService.isConnected()) {
        await pusherService.connect();
      }

      // Subscribe to observability metrics channel
      this.subscriptionId = pusherService.subscribe(
        'observability-metrics',
        (message: any) => {
          this.notifyListeners(message);
        }
      );

      this.isActive = true;
      console.log('Observability Pusher channel connected');
    } catch (error) {
      console.error('Failed to connect to Pusher channel:', error);
      throw error;
    }
  }

  disconnect() {
    if (this.subscriptionId) {
      pusherService.unsubscribe(this.subscriptionId);
      this.subscriptionId = null;
    }

    this.listeners.clear();
    this.isActive = false;
    console.log('Observability Pusher channel disconnected');
  }

  subscribe(callback: (data: any) => void) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners(data: any) {
    this.listeners.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Listener error:', error);
      }
    });
  }

  isConnected(): boolean {
    return this.isActive && pusherService.isConnected();
  }
}

// API client for observability endpoints
class ObservabilityAPI {
  private baseURL: string;
  private metricsPusher: MetricsPusherConnection;

  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1/observability`;
    this.metricsPusher = new MetricsPusherConnection();
  }

  // Metrics endpoints
  async getMetrics(timeRange: string = '1h', resolution: number = 60): Promise<MetricsResponse> {
    const response = await axios.get(`${this.baseURL}/metrics`, {
      params: { time_range: timeRange, resolution },
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Traces endpoints
  async getTraces(limit: number = 100, service?: string, minDurationMs?: number): Promise<{ data: { traces: Trace[] } }> {
    const response = await axios.get(`${this.baseURL}/traces`, {
      params: {
        limit,
        service,
        min_duration_ms: minDurationMs
      },
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getTraceDetails(traceId: string): Promise<{ data: { trace: Trace; correlatedTraces: Trace[] } }> {
    const response = await axios.get(`${this.baseURL}/trace/${traceId}`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Anomalies endpoints
  async getAnomalies(severity?: string, limit: number = 50): Promise<{ data: { anomalies: Anomaly[] } }> {
    const response = await axios.get(`${this.baseURL}/anomalies`, {
      params: { severity, limit },
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async acknowledgeAnomaly(anomalyId: string): Promise<void> {
    await axios.post(
      `${this.baseURL}/anomalies/acknowledge/${anomalyId}`,
      {},
      { headers: this.getAuthHeaders() }
    );
  }

  // Component health endpoints
  async getComponentHealth(): Promise<ComponentHealthResponse> {
    const response = await axios.get(`${this.baseURL}/health/components`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Prometheus metrics export
  async getPrometheusMetrics(): Promise<string> {
    const response = await axios.get(`${this.baseURL}/prometheus`, {
      headers: this.getAuthHeaders(),
      responseType: 'text'
    });
    return response.data;
  }

  // Pusher connection management
  async connectMetricsStream(onData: (data: any) => void): Promise<() => void> {
    try {
      await this.metricsPusher.connect();

      // Start the metrics streaming on the backend
      await axios.post(
        `${this.baseURL}/start-metrics-stream`,
        {},
        { headers: this.getAuthHeaders() }
      );

      return this.metricsPusher.subscribe(onData);
    } catch (error) {
      console.error('Failed to connect metrics stream:', error);
      throw error;
    }
  }

  async disconnectMetricsStream() {
    try {
      // Stop the metrics streaming on the backend
      await axios.post(
        `${this.baseURL}/stop-metrics-stream`,
        {},
        { headers: this.getAuthHeaders() }
      );
    } catch (error) {
      console.error('Failed to stop metrics stream:', error);
    } finally {
      this.metricsPusher.disconnect();
    }
  }

  isMetricsStreamConnected(): boolean {
    return this.metricsPusher.isConnected();
  }

  // Helper methods
  private getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Utility methods for data transformation
  formatDuration(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
    return `${(ms / 3600000).toFixed(1)}h`;
  }

  formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  }

  getHealthColor(status: string): string {
    switch (status) {
      case 'healthy': return '#4caf50';
      case 'degraded': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#9e9e9e';
    }
  }

  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'low': return '#2196f3';
      case 'medium': return '#ff9800';
      case 'high': return '#ff5722';
      case 'critical': return '#f44336';
      default: return '#9e9e9e';
    }
  }
}

// Export singleton instance
export const observabilityAPI = new ObservabilityAPI();

// Export convenience functions
export const {
  getMetrics,
  getTraces,
  getTraceDetails,
  getAnomalies,
  acknowledgeAnomaly,
  getComponentHealth,
  getPrometheusMetrics,
  connectMetricsStream,
  disconnectMetricsStream,
  isMetricsStreamConnected,
  formatDuration,
  formatBytes,
  getHealthColor,
  getSeverityColor
} = observabilityAPI;