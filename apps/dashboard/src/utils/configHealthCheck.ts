/**
 * Configuration Health Check Utility
 * Validates all critical dashboard configurations
 */

interface HealthCheckResult {
  status: 'healthy' | 'warning' | 'error';
  message: string;
  details?: any;
}

interface ConfigHealthReport {
  overall: 'healthy' | 'warning' | 'error';
  checks: {
    environment: HealthCheckResult;
    api: HealthCheckResult;
    websocket: HealthCheckResult;
    pusher: HealthCheckResult;
    auth: HealthCheckResult;
    performance: HealthCheckResult;
    security: HealthCheckResult;
  };
  timestamp: string;
  recommendations: string[];
}

class ConfigurationHealthCheck {
  private apiBaseUrl: string;
  private wsUrl: string;
  private pusherKey: string;
  private pusherCluster: string;
  private authEndpoint: string;

  constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
    this.wsUrl = import.meta.env.VITE_WS_URL || '';
    this.pusherKey = import.meta.env.VITE_PUSHER_KEY || '';
    this.pusherCluster = import.meta.env.VITE_PUSHER_CLUSTER || '';
    this.authEndpoint = import.meta.env.VITE_PUSHER_AUTH_ENDPOINT || '';
  }

  /**
   * Check environment configuration
   */
  private checkEnvironment(): HealthCheckResult {
    const requiredEnvVars = [
      'VITE_API_BASE_URL',
      'VITE_WS_URL',
      'VITE_PUSHER_KEY',
      'VITE_PUSHER_CLUSTER',
    ];

    const missingVars = requiredEnvVars.filter(
      varName => !import.meta.env[varName]
    );

    if (missingVars.length === 0) {
      return {
        status: 'healthy',
        message: 'All required environment variables are configured',
      };
    }

    return {
      status: 'error',
      message: `Missing environment variables: ${missingVars.join(', ')}`,
      details: { missingVars },
    };
  }

  /**
   * Check API connectivity
   */
  private async checkAPI(): Promise<HealthCheckResult> {
    if (!this.apiBaseUrl) {
      return {
        status: 'error',
        message: 'API base URL is not configured',
      };
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      // Use backend API URL for health check
      const response = await fetch(`${this.apiBaseUrl}/health`, {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        return {
          status: 'healthy',
          message: `API is reachable at ${this.apiBaseUrl}`,
        };
      }

      return {
        status: 'warning',
        message: `API responded with status ${response.status}`,
        details: { status: response.status },
      };
    } catch (error) {
      // Check if it's just a CORS issue (common in development)
      if (error instanceof TypeError && error.message.includes('fetch')) {
        return {
          status: 'warning',
          message: 'API might be running but CORS is blocking health check',
          details: {
            error: error.message,
            recommendation: 'This is normal in development if API is on different port'
          },
        };
      }

      return {
        status: 'error',
        message: `API is not reachable: ${error instanceof Error ? error.message : 'Unknown error'}`,
        details: { error },
      };
    }
  }

  /**
   * Check WebSocket configuration
   */
  private checkWebSocket(): HealthCheckResult {
    if (!this.wsUrl) {
      return {
        status: 'error',
        message: 'WebSocket URL is not configured',
      };
    }

    // Validate URL format
    try {
      new URL(this.wsUrl);
      return {
        status: 'healthy',
        message: `WebSocket configured at ${this.wsUrl}`,
      };
    } catch {
      return {
        status: 'error',
        message: 'Invalid WebSocket URL format',
        details: { wsUrl: this.wsUrl },
      };
    }
  }

  /**
   * Check Pusher configuration
   */
  private checkPusher(): HealthCheckResult {
    if (!this.pusherKey || !this.pusherCluster) {
      return {
        status: 'warning',
        message: 'Pusher is not fully configured',
        details: {
          hasKey: !!this.pusherKey,
          hasCluster: !!this.pusherCluster,
        },
      };
    }

    // Validate Pusher key format (should be 32 characters)
    if (this.pusherKey.length < 10) {
      return {
        status: 'warning',
        message: 'Pusher key seems invalid (too short)',
      };
    }

    return {
      status: 'healthy',
      message: 'Pusher is properly configured',
      details: {
        cluster: this.pusherCluster,
        authEndpoint: this.authEndpoint || 'Not configured',
      },
    };
  }

  /**
   * Check authentication configuration
   */
  private checkAuth(): HealthCheckResult {
    const token = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');
    const tokenExpiry = localStorage.getItem('tokenExpiry');

    if (!token) {
      return {
        status: 'warning',
        message: 'No authentication token found',
        details: { info: 'User might not be logged in' },
      };
    }

    // Check token expiry
    if (tokenExpiry) {
      const expiryTime = parseInt(tokenExpiry, 10);
      const now = Date.now();
      const timeLeft = expiryTime - now;

      if (timeLeft < 0) {
        return {
          status: 'warning',
          message: 'Authentication token has expired',
          details: {
            expired: true,
            hasRefreshToken: !!refreshToken,
          },
        };
      }

      if (timeLeft < 5 * 60 * 1000) { // Less than 5 minutes
        return {
          status: 'warning',
          message: 'Authentication token expires soon',
          details: {
            minutesLeft: Math.floor(timeLeft / 60000),
            hasRefreshToken: !!refreshToken,
          },
        };
      }
    }

    return {
      status: 'healthy',
      message: 'Authentication is properly configured',
      details: {
        hasToken: true,
        hasRefreshToken: !!refreshToken,
      },
    };
  }

  /**
   * Check performance configuration
   */
  private checkPerformance(): HealthCheckResult {
    const warnings: string[] = [];

    // Check if service worker is registered (for offline support)
    if ('serviceWorker' in navigator && !navigator.serviceWorker.controller) {
      warnings.push('Service Worker not registered');
    }

    // Check if too many background processes (non-standard API with feature detection)
    const perf = performance as any;
    if (perf.memory && perf.memory.usedJSHeapSize > 100 * 1024 * 1024) {
      warnings.push('High memory usage detected (>100MB)');
    }

    if (warnings.length === 0) {
      return {
        status: 'healthy',
        message: 'Performance configuration is optimal',
      };
    }

    return {
      status: 'warning',
      message: 'Performance could be improved',
      details: { warnings },
    };
  }

  /**
   * Check security configuration
   */
  private checkSecurity(): HealthCheckResult {
    const warnings: string[] = [];

    // Check if running on HTTPS (production)
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      warnings.push('Not running on HTTPS');
    }

    // Check if credentials are exposed in URL
    if (window.location.href.includes('password=') || window.location.href.includes('token=')) {
      warnings.push('Sensitive data detected in URL');
    }

    // Check localStorage for sensitive data
    const sensitiveKeys = ['password', 'secret', 'credit'];
    const localStorageKeys = Object.keys(localStorage);
    const exposedKeys = localStorageKeys.filter(key =>
      sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))
    );

    if (exposedKeys.length > 0) {
      warnings.push('Potentially sensitive data in localStorage');
    }

    if (warnings.length === 0) {
      return {
        status: 'healthy',
        message: 'Security configuration is good',
      };
    }

    return {
      status: 'warning',
      message: 'Security improvements recommended',
      details: { warnings },
    };
  }

  /**
   * Run all health checks
   */
  public async runHealthCheck(): Promise<ConfigHealthReport> {
    const checks = {
      environment: this.checkEnvironment(),
      api: await this.checkAPI(),
      websocket: this.checkWebSocket(),
      pusher: this.checkPusher(),
      auth: this.checkAuth(),
      performance: this.checkPerformance(),
      security: this.checkSecurity(),
    };

    // Determine overall health
    const statuses = Object.values(checks).map(check => check.status);
    let overall: 'healthy' | 'warning' | 'error' = 'healthy';

    if (statuses.includes('error')) {
      overall = 'error';
    } else if (statuses.includes('warning')) {
      overall = 'warning';
    }

    // Generate recommendations
    const recommendations: string[] = [];

    if (checks.environment.status !== 'healthy') {
      recommendations.push('Configure all required environment variables');
    }

    if (checks.api.status !== 'healthy') {
      recommendations.push('Ensure backend API is running and accessible');
    }

    if (checks.pusher.status !== 'healthy') {
      recommendations.push('Complete Pusher Channels configuration for real-time features');
    }

    if (checks.auth.status === 'warning') {
      recommendations.push('Implement automatic token refresh for seamless authentication');
    }

    if (checks.performance.status === 'warning') {
      recommendations.push('Consider implementing service workers for offline support');
    }

    if (checks.security.status === 'warning') {
      recommendations.push('Review security configuration and remove sensitive data from URLs/localStorage');
    }

    return {
      overall,
      checks,
      timestamp: new Date().toISOString(),
      recommendations,
    };
  }

  /**
   * Log health check results to console
   */
  public async logHealthCheck(): Promise<void> {
    const report = await this.runHealthCheck();

    console.group('🏥 Configuration Health Check');
    console.log(`Overall Status: ${report.overall.toUpperCase()}`);
    console.log(`Timestamp: ${report.timestamp}`);

    console.group('Checks:');
    Object.entries(report.checks).forEach(([name, check]) => {
      const emoji = check.status === 'healthy' ? '✅' : check.status === 'warning' ? '⚠️' : '❌';
      console.log(`${emoji} ${name}: ${check.message}`);
      if (check.details) {
        console.log('   Details:', check.details);
      }
    });
    console.groupEnd();

    if (report.recommendations.length > 0) {
      console.group('💡 Recommendations:');
      report.recommendations.forEach(rec => console.log(`• ${rec}`));
      console.groupEnd();
    }

    console.groupEnd();
  }
}

// Export singleton instance
export const configHealthCheck = new ConfigurationHealthCheck();

// Auto-run in development mode
if (import.meta.env.DEV) {
  // Run health check after app loads
  setTimeout(() => {
    configHealthCheck.logHealthCheck().catch(console.error);
  }, 2000);
}