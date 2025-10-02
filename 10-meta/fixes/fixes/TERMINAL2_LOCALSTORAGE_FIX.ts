// TERMINAL 2: Frontend LocalStorage and Verification Fixes
// File: src/dashboard/src/services/terminal-verify.ts
// REPLACE the problematic parts with this FIXED version

import axios, { AxiosInstance } from 'axios';
import io, { Socket } from 'socket.io-client';

interface VerificationResult {
  verificationId: string;
  timestamp: string;
  services: ServiceStatus[];
}

interface ServiceStatus {
  name: string;
  url: string;
  status: 'healthy' | 'degraded' | 'down';
  responseTime?: number;
  error?: string;
}

export class TerminalVerificationService {
  private verificationHistory: Map<string, VerificationResult> = new Map();
  private socket: Socket | null = null;
  private api: AxiosInstance;
  private maxHistorySize = 10; // Limit history to prevent memory issues

  constructor() {
    // Configure axios without User-Agent header (causes browser errors)
    this.api = axios.create({
      baseURL: 'http://localhost:8008',
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json',
        // Remove User-Agent - browsers don't allow setting it
      }
    });

    this.initializeSocketConnection();
  }

  private initializeSocketConnection() {
    // Connect to Socket.IO server
    this.socket = io('http://localhost:8008', {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      transports: ['websocket', 'polling'], // Try WebSocket first, fallback to polling
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to Terminal 1 via Socket.IO');
    });

    this.socket.on('verification_response', (data) => {
      console.log('📊 Verification response received:', data);
      this.handleVerificationResponse(data);
    });

    this.socket.on('connect_error', (error) => {
      console.warn('⚠️ Socket.IO connection error, using HTTP fallback');
      // Don't log full error to avoid console spam
    });
  }

  async runVerification(): Promise<VerificationResult> {
    const verificationId = `verify_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Define services to check
    const services: ServiceStatus[] = [
      { name: 'FastAPI', url: 'http://localhost:8008/health', status: 'down' },
      { name: 'API Status', url: 'http://localhost:8008/api/v1/status', status: 'down' },
      { name: 'Dashboard API', url: 'http://localhost:8008/api/v1/dashboard/overview', status: 'down' },
      { name: 'Auth Service', url: 'http://localhost:8008/auth/verify', status: 'down' },
      { name: 'WebSocket', url: 'ws://localhost:8008/ws', status: 'down' },
      { name: 'Socket.IO', url: 'http://localhost:8008/socket.io/', status: 'down' },
    ];

    // Check each service
    for (const service of services) {
      await this.verifyServiceEndpoint(service);
    }

    const result: VerificationResult = {
      verificationId,
      timestamp: new Date().toISOString(),
      services
    };

    // Store in memory map instead of localStorage (avoid quota issues)
    this.storeVerificationResult(result);

    // Send to Terminal 1
    await this.sendVerificationToTerminal1(result);

    return result;
  }

  private async verifyServiceEndpoint(service: ServiceStatus): Promise<void> {
    const startTime = Date.now();
    
    try {
      if (service.url.startsWith('ws://')) {
        // WebSocket check
        service.status = await this.checkWebSocket(service.url) ? 'healthy' : 'down';
      } else {
        // HTTP check
        const response = await this.api.get(service.url);
        service.status = response.status === 200 ? 'healthy' : 'degraded';
        service.responseTime = Date.now() - startTime;
      }
    } catch (error) {
      service.status = 'down';
      service.error = error instanceof Error ? error.message : 'Unknown error';
      // Don't log full error to reduce console noise
    }
  }

  private async checkWebSocket(url: string): Promise<boolean> {
    return new Promise((resolve) => {
      const ws = new WebSocket(url);
      const timeout = setTimeout(() => {
        ws.close();
        resolve(false);
      }, 2000);

      ws.onopen = () => {
        clearTimeout(timeout);
        ws.close();
        resolve(true);
      };

      ws.onerror = () => {
        clearTimeout(timeout);
        resolve(false);
      };
    });
  }

  private storeVerificationResult(result: VerificationResult) {
    // Store in memory map
    this.verificationHistory.set(result.verificationId, result);
    
    // Limit history size to prevent memory issues
    if (this.verificationHistory.size > this.maxHistorySize) {
      const firstKey = this.verificationHistory.keys().next().value;
      if (firstKey) {
        this.verificationHistory.delete(firstKey);
      }
    }

    // Store minimal data in localStorage (just the ID and timestamp)
    try {
      const minimalData = {
        id: result.verificationId,
        timestamp: result.timestamp,
        healthy: result.services.filter(s => s.status === 'healthy').length,
        total: result.services.length
      };
      
      // Store only recent verification IDs
      const recentVerifications = this.getRecentVerifications();
      recentVerifications.push(minimalData);
      
      // Keep only last 5 verifications in localStorage
      if (recentVerifications.length > 5) {
        recentVerifications.shift();
      }
      
      localStorage.setItem('recent_verifications', JSON.stringify(recentVerifications));
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

  private clearOldLocalStorageData() {
    // Clear old terminal verification data
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('terminal_verification_')) {
        localStorage.removeItem(key);
      }
    });
    
    console.log('✅ Cleared old localStorage data to free up space');
  }

  private async sendVerificationToTerminal1(result: VerificationResult) {
    const summary = {
      verificationId: result.verificationId,
      totalServices: result.services.length,
      healthyServices: result.services.filter(s => s.status === 'healthy').length,
      degradedServices: result.services.filter(s => s.status === 'degraded').length,
      downServices: result.services.filter(s => s.status === 'down').length,
      timestamp: result.timestamp
    };

    console.log('📊 Terminal 2 → Terminal 1:', summary);

    // Try Socket.IO first
    if (this.socket && this.socket.connected) {
      this.socket.emit('verification_update', summary);
      return;
    }

    // Fallback to HTTP
    try {
      await this.api.post('/api/v1/terminal/verification', summary);
    } catch (error) {
      // Don't log full error, just note the failure
      console.warn('⚠️ Could not send verification to Terminal 1');
    }
  }

  private handleVerificationResponse(data: any) {
    console.log('✅ Verification acknowledged by Terminal 1:', data.verificationId);
  }

  startMonitoring(intervalMs: number = 30000) {
    console.log(`🎯 Starting Terminal 2 verification monitoring`);
    
    // Run initial verification
    this.runVerification().catch(err => {
      console.warn('⚠️ Initial verification failed');
    });

    // Set up periodic verification
    setInterval(() => {
      this.runVerification().catch(err => {
        console.warn('⚠️ Periodic verification failed');
      });
    }, intervalMs);

    console.log(`✅ Monitoring started with ${intervalMs}ms interval`);
  }

  cleanup() {
    if (this.socket) {
      this.socket.disconnect();
    }
    this.verificationHistory.clear();
    this.clearOldLocalStorageData();
  }
}

// Export singleton instance
export const terminalVerify = new TerminalVerificationService();