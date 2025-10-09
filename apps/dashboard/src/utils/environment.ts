/**
 * Environment Detection and Configuration Utility
 *
 * This module provides a centralized way to detect and manage
 * the current environment (development, staging, production)
 * and determine data source (mock vs real API)
 */

export type Environment = 'development' | 'staging' | 'production';
export type DataSource = 'mock' | 'api';

interface EnvironmentConfig {
  environment: Environment;
  dataSource: DataSource;
  apiBaseUrl: string;
  mockDelay: number;
  bypassAuth: boolean;
  debug: boolean;
  pusherEnabled: boolean;
}

/**
 * Get the current environment based on Vite env variables
 */
export function getCurrentEnvironment(): Environment {
  const env = import.meta.env.VITE_ENV as Environment;

  // Default to development if not specified
  if (!env || !['development', 'staging', 'production'].includes(env)) {
    return 'development';
  }

  return env;
}

/**
 * Determine the data source based on environment and configuration
 */
export function getDataSource(): DataSource {
  // Explicit mock mode takes precedence
  if (import.meta.env.VITE_USE_MOCK_DATA === 'true') {
    return 'mock';
  }

  // In development with bypass auth, use mock data
  if (getCurrentEnvironment() === 'development' &&
      import.meta.env.VITE_BYPASS_AUTH === 'true') {
    return 'mock';
  }

  // Production and staging always use real API
  if (getCurrentEnvironment() === 'production' ||
      getCurrentEnvironment() === 'staging') {
    return 'api';
  }

  // Default to mock for development
  return getCurrentEnvironment() === 'development' ? 'mock' : 'api';
}

/**
 * Get the complete environment configuration
 */
export function getEnvironmentConfig(): EnvironmentConfig {
  return {
    environment: getCurrentEnvironment(),
    dataSource: getDataSource(),
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8009',
    mockDelay: parseInt(import.meta.env.VITE_MOCK_DELAY || '300', 10),
    bypassAuth: import.meta.env.VITE_BYPASS_AUTH === 'true',
    debug: import.meta.env.VITE_ENABLE_DEBUG === 'true',
    pusherEnabled: import.meta.env.VITE_ENABLE_PUSHER === 'true',
  };
}

/**
 * Check if we're in development mode
 */
export function isDevelopment(): boolean {
  return getCurrentEnvironment() === 'development';
}

/**
 * Check if we're in production mode
 */
export function isProduction(): boolean {
  return getCurrentEnvironment() === 'production';
}

/**
 * Check if we're in staging mode
 */
export function isStaging(): boolean {
  return getCurrentEnvironment() === 'staging';
}

/**
 * Check if we're using mock data
 */
export function isMockMode(): boolean {
  return getDataSource() === 'mock';
}

/**
 * Check if we're using real API
 */
export function isApiMode(): boolean {
  return getDataSource() === 'api';
}

/**
 * Check if debug mode is enabled
 */
export function isDebugMode(): boolean {
  return getEnvironmentConfig().debug;
}

/**
 * Log debug information if debug mode is enabled
 */
export function debugLog(message: string, ...args: any[]): void {
  if (isDebugMode()) {
    console.log(`[DEBUG ${getCurrentEnvironment()}] ${message}`, ...args);
  }
}

/**
 * Get a descriptive string of the current configuration
 */
export function getEnvironmentDescription(): string {
  const config = getEnvironmentConfig();
  return `Environment: ${config.environment} | Data: ${config.dataSource} | API: ${config.apiBaseUrl}`;
}

// Export a singleton config object for easy access
export const envConfig = getEnvironmentConfig();

// Log environment on initialization (only in debug mode)
if (isDebugMode()) {
  console.log('🌍 Environment Configuration:', {
    ...envConfig,
    description: getEnvironmentDescription(),
  });
}