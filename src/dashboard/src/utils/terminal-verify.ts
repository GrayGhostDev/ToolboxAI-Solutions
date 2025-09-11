/**
 * Terminal Verification Service for Terminal 2
 * 
 * Comprehensive service to verify Terminal 1's services and report back
 * Implements real-time monitoring, error handling, and cross-terminal communication
 * 
 * @fileoverview Production-ready terminal verification with Socket.io and axios integration
 * @version 1.0.0
 */

import { io, Socket } from 'socket.io-client';
import axios, { AxiosInstance, AxiosError } from 'axios';
import { API_BASE_URL, WS_URL, AUTH_TOKEN_KEY } from '../config';

// ================================
// TYPE DEFINITIONS
// ================================

export interface VerificationResult {
  service: string;
  status: 'healthy' | 'degraded' | 'down' | 'unauthorized';
  latency: number;
  timestamp: string;
  details?: {
    responseCode?: number;
    errorMessage?: string;
    timeout?: boolean;
    retryCount?: number;
  };
}

export interface ServiceEndpoint {
  name: string;
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  expectedStatus?: number;
  timeout?: number;
  headers?: Record<string, string>;
  payload?: any;
  critical?: boolean;
}

export interface DashboardStatus {
  running: boolean;
  port: number;
  components_loaded: number;
  errors: string[];
  memory_usage?: number;
  cpu_usage?: number;
  build_timestamp?: string;
  version?: string;
}

export interface TerminalMessage {
  from: 'terminal2';
  to: 'terminal1' | 'all';
  timestamp: string;
  type: 'verification_response' | 'health_check' | 'error_report' | 'status_update';
  payload: {
    services: VerificationResult[];
    dashboard_status: DashboardStatus;
    metadata?: {
      verification_id?: string;
      sequence_number?: number;
      requires_response?: boolean;
    };
  };
}

export interface VerificationConfig {
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  healthCheckInterval: number;
  enableRealTimeMonitoring: boolean;
  criticalServicesOnly: boolean;
}

// ================================
// VERIFICATION SERVICE
// ================================

class TerminalVerificationService {
  private static instance: TerminalVerificationService | null = null;
  private socket: Socket | null = null;
  private apiClient: AxiosInstance;
  private config: VerificationConfig;
  private verificationTimer: NodeJS.Timeout | null = null;
  private isRunning: boolean = false;
  // private lastVerificationId: string = '';
  private consoleErrors: string[] = [];
  private performanceMetrics: Map<string, number> = new Map();
  private verificationHistory: Map<string, any> = new Map();
  private maxHistorySize = 10; // Limit history to prevent memory issues

  // Service endpoints to verify
  private readonly serviceEndpoints: ServiceEndpoint[] = [
    {
      name: 'Health Check',
      path: '/health',
      method: 'GET',
      expectedStatus: 200,
      timeout: 5000,
      critical: true
    },
    {
      name: 'API Status',
      path: '/api/v1/status',
      method: 'GET',
      expectedStatus: 200,
      timeout: 3000,
      critical: true
    },
    {
      name: 'Authentication Endpoint',
      path: '/auth/verify',
      method: 'POST',
      expectedStatus: 401, // Expected for test credentials
      timeout: 5000,
      payload: { username: 'test_user', password: 'invalid' },
      critical: true
    },
    {
      name: 'User Management',
      path: '/api/v1/users/me',
      method: 'GET',
      expectedStatus: 401, // Without proper auth
      timeout: 3000,
      critical: false
    },
    {
      name: 'Dashboard Data',
      path: '/api/v1/dashboard/overview',
      method: 'GET',
      expectedStatus: 401, // Without proper auth
      timeout: 5000,
      critical: false
    },
    {
      name: 'Content Generation',
      path: '/api/v1/content/generate',
      method: 'POST',
      expectedStatus: 401, // Without proper auth
      timeout: 10000,
      critical: false
    },
    {
      name: 'WebSocket Endpoint',
      path: '/socket.io',
      method: 'GET',
      expectedStatus: 200,
      timeout: 5000,
      critical: true
    }
  ];

  constructor(config: Partial<VerificationConfig> = {}) {
    this.config = {
      timeout: 10000,
      retryAttempts: 3,
      retryDelay: 1000,
      healthCheckInterval: 30000, // 30 seconds
      enableRealTimeMonitoring: true,
      criticalServicesOnly: false,
      ...config
    };

    // Initialize axios client with interceptors
    this.apiClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json'
        // Remove User-Agent - browsers don't allow setting it
      }
    });

    this.setupAxiosInterceptors();
    this.initializeConsoleErrorCapture();
    this.initializePerformanceMonitoring();
  }

  // ================================
  // SINGLETON PATTERN
  // ================================

  public static getInstance(config?: Partial<VerificationConfig>): TerminalVerificationService {
    if (!TerminalVerificationService.instance) {
      TerminalVerificationService.instance = new TerminalVerificationService(config);
    }
    return TerminalVerificationService.instance;
  }

  // ================================
  // INITIALIZATION METHODS
  // ================================

  private setupAxiosInterceptors(): void {
    // Request interceptor
    this.apiClient.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(AUTH_TOKEN_KEY);
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Track request start time
        (config as any).metadata = { startTime: Date.now() };
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.apiClient.interceptors.response.use(
      (response) => {
        const startTime = (response.config as any).metadata?.startTime;
        if (startTime) {
          const latency = Date.now() - startTime;
          this.performanceMetrics.set(response.config.url || 'unknown', latency);
        }
        return response;
      },
      (error) => {
        const startTime = (error.config as any)?.metadata?.startTime;
        if (startTime) {
          const latency = Date.now() - startTime;
          this.performanceMetrics.set(error.config?.url || 'unknown', latency);
        }
        return Promise.reject(error);
      }
    );
  }

  private initializeConsoleErrorCapture(): void {
    const originalError = console.error;
    console.error = (...args: any[]) => {
      const errorMessage = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ');
      
      this.consoleErrors.push(`[${new Date().toISOString()}] ${errorMessage}`);
      
      // Keep only last 50 errors
      if (this.consoleErrors.length > 50) {
        this.consoleErrors.shift();
      }
      
      originalError.apply(console, args);
    };
  }

  private initializePerformanceMonitoring(): void {
    if (typeof window !== 'undefined') {
      // Monitor page visibility changes
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && this.config.enableRealTimeMonitoring) {
          this.runVerification();
        }
      });

      // Monitor network status changes
      window.addEventListener('online', () => {
        console.log('🌐 Network connection restored - running verification');
        this.runVerification();
      });

      window.addEventListener('offline', () => {
        console.warn('🌐 Network connection lost');
        this.stopMonitoring();
      });
    }
  }

  // ================================
  // MAIN VERIFICATION METHODS
  // ================================

  public async runVerification(): Promise<VerificationResult[]> {
    const verificationId = this.generateVerificationId();
    // this.lastVerificationId = verificationId;
    
    console.log(`🔍 Starting verification ${verificationId}`);
    
    const results: VerificationResult[] = [];
    const servicesToVerify = this.config.criticalServicesOnly 
      ? this.serviceEndpoints.filter(s => s.critical)
      : this.serviceEndpoints;

    // Run service verifications in parallel for better performance
    const verificationPromises = servicesToVerify.map(endpoint => 
      this.verifyServiceEndpoint(endpoint)
    );

    // Add WebSocket verification
    verificationPromises.push(this.verifyWebSocket());

    try {
      const verificationResults = await Promise.allSettled(verificationPromises);
      
      verificationResults.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          results.push(result.value);
        } else {
          const serviceName = index < servicesToVerify.length 
            ? servicesToVerify[index].name 
            : 'WebSocket';
            
          results.push({
            service: serviceName,
            status: 'down',
            latency: 0,
            timestamp: new Date().toISOString(),
            details: {
              errorMessage: result.reason?.message || 'Unknown error',
              timeout: false,
              retryCount: 0
            }
          });
        }
      });

      // Send results to Terminal 1
      await this.sendVerificationToTerminal1(results, verificationId);
      
      console.log(`✅ Verification ${verificationId} completed with ${results.length} results`);
      
      return results;
      
    } catch (error) {
      console.error('❌ Verification failed:', error);
      throw error;
    }
  }

  private async verifyServiceEndpoint(endpoint: ServiceEndpoint): Promise<VerificationResult> {
    const startTime = Date.now();
    let retryCount = 0;
    
    const attemptVerification = async (): Promise<VerificationResult> => {
      try {
        const response = await this.apiClient.request({
          method: endpoint.method,
          url: endpoint.path,
          timeout: endpoint.timeout || this.config.timeout,
          data: endpoint.payload,
          headers: endpoint.headers,
          validateStatus: () => true // Don't throw on HTTP error codes
        });

        const latency = Date.now() - startTime;
        const expectedStatus = endpoint.expectedStatus || 200;
        
        let status: VerificationResult['status'];
        if (response.status === expectedStatus) {
          status = 'healthy';
        } else if (response.status >= 500) {
          status = 'down';
        } else if (response.status === 401 || response.status === 403) {
          status = endpoint.name.includes('Auth') ? 'healthy' : 'unauthorized';
        } else {
          status = 'degraded';
        }

        return {
          service: endpoint.name,
          status,
          latency,
          timestamp: new Date().toISOString(),
          details: {
            responseCode: response.status,
            retryCount,
            timeout: false
          }
        };

      } catch (error) {
        const latency = Date.now() - startTime;
        const axiosError = error as AxiosError;
        
        // Retry logic for network errors
        if (retryCount < this.config.retryAttempts && 
            (axiosError.code === 'ECONNREFUSED' || axiosError.code === 'ENOTFOUND')) {
          retryCount++;
          console.warn(`🔄 Retrying ${endpoint.name} (attempt ${retryCount}/${this.config.retryAttempts})`);
          await this.delay(this.config.retryDelay * retryCount); // Exponential backoff
          return attemptVerification();
        }

        return {
          service: endpoint.name,
          status: 'down',
          latency,
          timestamp: new Date().toISOString(),
          details: {
            errorMessage: axiosError.message,
            responseCode: axiosError.response?.status,
            timeout: axiosError.code === 'ECONNABORTED',
            retryCount
          }
        };
      }
    };

    return attemptVerification();
  }

  private async verifyWebSocket(): Promise<VerificationResult> {
    const startTime = Date.now();
    
    return new Promise((resolve) => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      let isResolved = false;
      
      try {
        const testSocket = io(WS_URL, {
          auth: { token },
          transports: ['websocket', 'polling'],
          path: '/socket.io',
          timeout: 5000,
          reconnection: false
        });

        const cleanup = () => {
          if (!isResolved) {
            isResolved = true;
            testSocket.disconnect();
          }
        };

        const timeout = setTimeout(() => {
          cleanup();
          resolve({
            service: 'WebSocket Connection',
            status: 'down',
            latency: Date.now() - startTime,
            timestamp: new Date().toISOString(),
            details: {
              errorMessage: 'Connection timeout',
              timeout: true,
              retryCount: 0
            }
          });
        }, 5000);

        testSocket.on('connect', () => {
          clearTimeout(timeout);
          cleanup();
          resolve({
            service: 'WebSocket Connection',
            status: 'healthy',
            latency: Date.now() - startTime,
            timestamp: new Date().toISOString(),
            details: {
              timeout: false,
              retryCount: 0
            }
          });
        });

        testSocket.on('connect_error', (error) => {
          clearTimeout(timeout);
          cleanup();
          resolve({
            service: 'WebSocket Connection',
            status: 'down',
            latency: Date.now() - startTime,
            timestamp: new Date().toISOString(),
            details: {
              errorMessage: error.message,
              timeout: false,
              retryCount: 0
            }
          });
        });

      } catch (error) {
        if (!isResolved) {
          resolve({
            service: 'WebSocket Connection',
            status: 'down',
            latency: Date.now() - startTime,
            timestamp: new Date().toISOString(),
            details: {
              errorMessage: (error as Error).message,
              timeout: false,
              retryCount: 0
            }
          });
        }
      }
    });
  }

  // ================================
  // COMMUNICATION METHODS
  // ================================

  private async sendVerificationToTerminal1(
    results: VerificationResult[], 
    verificationId: string
  ): Promise<void> {
    const dashboardStatus = this.getDashboardStatus();
    
    const message: TerminalMessage = {
      from: 'terminal2',
      to: 'terminal1',
      timestamp: new Date().toISOString(),
      type: 'verification_response',
      payload: {
        services: results,
        dashboard_status: dashboardStatus,
        metadata: {
          verification_id: verificationId,
          sequence_number: this.getSequenceNumber(),
          requires_response: false
        }
      }
    };

    // Log the verification results
    console.log('📊 Terminal 2 → Terminal 1:', {
      verificationId,
      totalServices: results.length,
      healthyServices: results.filter(r => r.status === 'healthy').length,
      degradedServices: results.filter(r => r.status === 'degraded').length,
      downServices: results.filter(r => r.status === 'down').length,
      averageLatency: this.calculateAverageLatency(results)
    });

    try {
      // Send via WebSocket if available
      await this.sendViaWebSocket(message);
    } catch (error) {
      console.warn('⚠️ WebSocket send failed, using fallback methods:', error);
      await this.sendViaFallbackMethods(message);
    }
  }

  private async sendViaWebSocket(message: TerminalMessage): Promise<void> {
    if (!this.socket || !this.socket.connected) {
      await this.establishWebSocketConnection();
    }

    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        this.socket.emit('terminal:verify', message, (acknowledgment: any) => {
          if (acknowledgment && acknowledgment.success) {
            console.log('✅ Verification sent to Terminal 1 via WebSocket');
            resolve();
          } else {
            reject(new Error('WebSocket send not acknowledged'));
          }
        });

        // Timeout the acknowledgment wait
        setTimeout(() => {
          reject(new Error('WebSocket acknowledgment timeout'));
        }, 5000);
      } else {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  private async sendViaFallbackMethods(message: TerminalMessage): Promise<void> {
    try {
      // Try HTTP POST to Terminal 1
      await this.apiClient.post('/api/v1/terminal/verification', message, {
        timeout: 3000
      });
      console.log('✅ Verification sent to Terminal 1 via HTTP');
    } catch (httpError) {
      console.warn('⚠️ HTTP send failed, using memory storage with minimal localStorage');
      
      // Store in memory map instead of localStorage to avoid quota issues
      this.storeVerificationResult(message);
    }
  }

  private storeVerificationResult(message: TerminalMessage): void {
    const verificationId = message.payload.metadata?.verification_id || `verify_${Date.now()}`;
    
    // Store in memory map
    this.verificationHistory.set(verificationId, message);
    
    // Limit history size to prevent memory issues
    if (this.verificationHistory.size > this.maxHistorySize) {
      const firstKey = this.verificationHistory.keys().next().value;
      if (firstKey) {
        this.verificationHistory.delete(firstKey);
      }
    }

    // Store minimal data in localStorage (just the ID and summary)
    try {
      const minimalData = {
        id: verificationId,
        timestamp: message.timestamp,
        healthy: message.payload.services.filter(s => s.status === 'healthy').length,
        total: message.payload.services.length
      };
      
      // Store only recent verification IDs
      const recentVerifications = this.getRecentVerifications();
      recentVerifications.push(minimalData);
      
      // Keep only last 5 verifications in localStorage
      if (recentVerifications.length > 5) {
        recentVerifications.shift();
      }
      
      localStorage.setItem('recent_verifications', JSON.stringify(recentVerifications));
      console.log('📁 Verification stored in memory:', verificationId);
    } catch (e) {
      // If localStorage is full, clear old data
      if (e instanceof DOMException && e.name === 'QuotaExceededError') {
        this.clearOldLocalStorageData();
      }
    }
  }

  private getRecentVerifications(): any[] {
    try {
      const data = localStorage.getItem('recent_verifications');
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  private clearOldLocalStorageData(): void {
    // Clear old terminal verification data
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('terminal_verification_')) {
        localStorage.removeItem(key);
      }
    });
    
    console.log('✅ Cleared old localStorage data to free up space');
  }

  private async establishWebSocketConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      
      this.socket = io(WS_URL, {
        auth: { token },
        transports: ['websocket', 'polling'],
        path: '/socket.io',
        timeout: 10000
      });

      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, 10000);

      this.socket.on('connect', () => {
        clearTimeout(timeout);
        console.log('✅ Terminal verification WebSocket connected');
        resolve();
      });

      this.socket.on('connect_error', (error) => {
        clearTimeout(timeout);
        console.error('❌ WebSocket connection error:', error);
        reject(error);
      });
    });
  }

  // ================================
  // MONITORING METHODS
  // ================================

  public startMonitoring(): void {
    if (this.isRunning) {
      console.warn('⚠️ Monitoring is already running');
      return;
    }

    console.log('🎯 Starting Terminal 2 verification monitoring');
    this.isRunning = true;

    // Run initial verification
    this.runVerification().catch(error => {
      console.error('❌ Initial verification failed:', error);
    });

    // Set up periodic verification
    this.verificationTimer = setInterval(() => {
      if (this.isRunning) {
        this.runVerification().catch(error => {
          console.error('❌ Periodic verification failed:', error);
        });
      }
    }, this.config.healthCheckInterval);

    console.log(`✅ Monitoring started with ${this.config.healthCheckInterval}ms interval`);
  }

  public stopMonitoring(): void {
    if (!this.isRunning) {
      return;
    }

    console.log('🛑 Stopping Terminal 2 verification monitoring');
    this.isRunning = false;

    if (this.verificationTimer) {
      clearInterval(this.verificationTimer);
      this.verificationTimer = null;
    }

    if (this.socket?.connected) {
      this.socket.disconnect();
      this.socket = null;
    }

    // Clear memory storage
    this.verificationHistory.clear();
    
    // Clean up old localStorage data
    this.clearOldLocalStorageData();

    console.log('✅ Monitoring stopped and memory cleared');
  }

  // ================================
  // UTILITY METHODS
  // ================================

  private getDashboardStatus(): DashboardStatus {
    const port = this.getCurrentPort();
    const componentsLoaded = this.countLoadedComponents();
    
    return {
      running: true,
      port,
      components_loaded: componentsLoaded,
      errors: [...this.consoleErrors],
      memory_usage: this.getMemoryUsage(),
      cpu_usage: this.getCPUUsage(),
      build_timestamp: this.getBuildTimestamp(),
      version: this.getVersion()
    };
  }

  private getCurrentPort(): number {
    if (typeof window !== 'undefined') {
      return parseInt(window.location.port) || (window.location.protocol === 'https:' ? 443 : 80);
    }
    return 5179; // Default Vite dev server port
  }

  private countLoadedComponents(): number {
    if (typeof document !== 'undefined') {
      const reactComponents = document.querySelectorAll('[data-component]').length;
      const reactRootComponents = document.querySelectorAll('[data-reactroot]').length;
      const customComponents = document.querySelectorAll('[data-testid]').length;
      
      return Math.max(reactComponents, reactRootComponents, customComponents);
    }
    return 0;
  }

  private getMemoryUsage(): number {
    if (typeof performance !== 'undefined' && 'memory' in performance) {
      const memory = (performance as any).memory;
      return Math.round(memory.usedJSHeapSize / 1024 / 1024); // MB
    }
    return 0;
  }

  private getCPUUsage(): number {
    // This is a simplified CPU usage estimation
    // In a real implementation, you might use performance.measure()
    const performanceEntries = performance.getEntriesByType('measure');
    const recentEntries = performanceEntries.filter(entry => 
      Date.now() - entry.startTime < 30000 // Last 30 seconds
    );
    
    if (recentEntries.length === 0) return 0;
    
    const avgDuration = recentEntries.reduce((sum, entry) => sum + entry.duration, 0) / recentEntries.length;
    return Math.min(Math.round(avgDuration / 10), 100); // Normalize to 0-100%
  }

  private getBuildTimestamp(): string {
    // Try to get build timestamp from various sources
    if (typeof document !== 'undefined') {
      const metaTag = document.querySelector('meta[name="build-timestamp"]');
      if (metaTag) {
        return metaTag.getAttribute('content') || new Date().toISOString();
      }
    }
    
    return new Date().toISOString();
  }

  private getVersion(): string {
    // Try to get version from various sources
    if (typeof document !== 'undefined') {
      const metaTag = document.querySelector('meta[name="version"]');
      if (metaTag) {
        return metaTag.getAttribute('content') || '1.0.0';
      }
    }
    
    return '1.0.0';
  }

  private calculateAverageLatency(results: VerificationResult[]): number {
    const validLatencies = results
      .map(r => r.latency)
      .filter(l => l > 0);
    
    if (validLatencies.length === 0) return 0;
    
    return Math.round(
      validLatencies.reduce((sum, latency) => sum + latency, 0) / validLatencies.length
    );
  }

  private generateVerificationId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 15);
    return `verify_${timestamp}_${random}`;
  }

  private getSequenceNumber(): number {
    const current = parseInt(localStorage.getItem('terminal2_sequence') || '0');
    const next = current + 1;
    localStorage.setItem('terminal2_sequence', next.toString());
    return next;
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ================================
  // PUBLIC API METHODS
  // ================================

  public getLastVerificationResults(): Promise<VerificationResult[]> {
    return this.runVerification();
  }

  public getHealthSummary(): {
    isHealthy: boolean;
    totalServices: number;
    healthyServices: number;
    lastCheck: string;
  } {
    return {
      isHealthy: this.isRunning,
      totalServices: this.serviceEndpoints.length,
      healthyServices: 0, // Would be updated from last verification
      lastCheck: new Date().toISOString()
    };
  }

  public updateConfig(newConfig: Partial<VerificationConfig>): void {
    this.config = { ...this.config, ...newConfig };
    console.log('⚙️ Verification config updated:', this.config);
    
    // Restart monitoring with new config
    if (this.isRunning) {
      this.stopMonitoring();
      this.startMonitoring();
    }
  }

  public isMonitoring(): boolean {
    return this.isRunning;
  }

  public getPerformanceMetrics(): Map<string, number> {
    return new Map(this.performanceMetrics);
  }

  public clearConsoleErrors(): void {
    this.consoleErrors = [];
    console.log('🧹 Console errors cleared');
  }
}

// ================================
// EXPORT SINGLETON INSTANCE
// ================================

export default TerminalVerificationService;

// Create and export the singleton instance
export const terminalVerifier = TerminalVerificationService.getInstance();

// Auto-start monitoring in development mode
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  console.log('🚀 Terminal verification service initialized');
  
  // Start monitoring after a short delay to ensure app is loaded
  setTimeout(() => {
    terminalVerifier.startMonitoring();
  }, 2000);
}