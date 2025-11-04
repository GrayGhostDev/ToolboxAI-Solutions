/**
 * Backend Health Check Utility
 * Prevents infinite loading by verifying backend availability before authentication
 */

import { logger } from './logger';
import { endpoints } from '../config/api';

export interface HealthCheckResult {
  isHealthy: boolean;
  responseTime?: number;
  error?: string;
  timestamp: number;
}

/**
 * Check if the backend API is reachable and healthy
 * @param timeoutMs - Maximum time to wait for health check (default 3 seconds)
 * @returns Promise<HealthCheckResult>
 */
export const checkBackendHealth = async (
  timeoutMs: number = 3000
): Promise<HealthCheckResult> => {
  const startTime = Date.now();
  const controller = new AbortController();

  // Set timeout for the fetch request
  const timeout = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    logger.debug('Starting backend health check', {
      endpoint: endpoints.health,
      timeout: timeoutMs
    });

    const response = await fetch(endpoints.health, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
      // Don't send credentials for health check
      credentials: 'omit',
    });

    clearTimeout(timeout);
    const responseTime = Date.now() - startTime;

    if (response.ok) {
      logger.info('Backend health check passed', {
        responseTime: `${responseTime}ms`,
        status: response.status
      });

      return {
        isHealthy: true,
        responseTime,
        timestamp: Date.now(),
      };
    } else {
      const error = `Backend returned ${response.status} ${response.statusText}`;
      logger.warn('Backend health check failed', {
        error,
        responseTime: `${responseTime}ms`
      });

      return {
        isHealthy: false,
        responseTime,
        error,
        timestamp: Date.now(),
      };
    }
  } catch (error: any) {
    clearTimeout(timeout);
    const responseTime = Date.now() - startTime;

    // Determine error type
    let errorMessage = 'Unknown error';
    if (error.name === 'AbortError') {
      errorMessage = `Backend health check timed out after ${timeoutMs}ms`;
    } else if (error.message?.includes('fetch')) {
      errorMessage = 'Network error - backend unreachable';
    } else {
      errorMessage = error.message || 'Backend health check failed';
    }

    // Use debug level for timeouts and network errors (common in dev when backend is off)
    // Only use error level for truly unexpected errors
    const isExpectedError = error.name === 'AbortError' ||
                           errorMessage.includes('Network error') ||
                           errorMessage.includes('CORS') ||
                           errorMessage.includes('Failed to fetch');

    const logLevel = isExpectedError ? 'debug' : 'error';
    logger[logLevel]('Backend health check failed', {
      error: errorMessage,
      responseTime: `${responseTime}ms`,
      details: isExpectedError ? undefined : error
    });

    return {
      isHealthy: false,
      responseTime,
      error: errorMessage,
      timestamp: Date.now(),
    };
  }
};

/**
 * Retry health check with exponential backoff
 * @param maxRetries - Maximum number of retry attempts (default 3)
 * @param initialDelay - Initial delay in ms before first retry (default 1000ms)
 * @returns Promise<HealthCheckResult>
 */
export const checkBackendHealthWithRetry = async (
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<HealthCheckResult> => {
  let lastResult: HealthCheckResult | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    logger.debug(`Health check attempt ${attempt + 1}/${maxRetries + 1}`);

    const result = await checkBackendHealth();
    lastResult = result;

    if (result.isHealthy) {
      return result;
    }

    // Don't delay after the last attempt
    if (attempt < maxRetries) {
      const delay = initialDelay * Math.pow(2, attempt); // Exponential backoff
      logger.debug(`Retrying health check in ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  return lastResult!;
};

/**
 * Get user-friendly message based on health check result
 */
export const getHealthCheckMessage = (result: HealthCheckResult): string => {
  if (result.isHealthy) {
    return 'Backend is operational';
  }

  if (result.error?.includes('timeout')) {
    return 'Backend is taking too long to respond. It may be starting up.';
  }

  if (result.error?.includes('Network error')) {
    return 'Cannot reach the backend server. Please check your internet connection.';
  }

  return result.error || 'Backend is temporarily unavailable';
};
