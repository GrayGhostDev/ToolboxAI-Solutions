/**
 * ============================================
 * useBackendHealth Hook
 * ============================================
 * Monitors backend API health status with automatic polling
 * Provides real-time connectivity feedback to components
 * ============================================
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { logger } from '../utils/logger';

export type BackendHealthStatus = 'checking' | 'online' | 'offline';

export interface BackendHealthResult {
  status: BackendHealthStatus;
  lastChecked: Date | null;
  error: string | null;
  responseTime: number | null;
}

interface UseBackendHealthOptions {
  /**
   * Polling interval in milliseconds
   * @default 30000 (30 seconds)
   */
  pollInterval?: number;

  /**
   * Enable automatic polling
   * @default true
   */
  enablePolling?: boolean;

  /**
   * Health check endpoint
   * @default '/health'
   */
  healthEndpoint?: string;

  /**
   * Request timeout in milliseconds
   * @default 5000
   */
  timeout?: number;
}

/**
 * Custom hook for monitoring backend health status
 *
 * @example
 * ```tsx
 * const { status, lastChecked, checkHealth } = useBackendHealth();
 *
 * if (status === 'offline') {
 *   return <Alert>Backend is currently unavailable</Alert>;
 * }
 * ```
 */
export function useBackendHealth(options: UseBackendHealthOptions = {}): BackendHealthResult & {
  checkHealth: () => Promise<void>;
} {
  const {
    pollInterval = 30000,
    enablePolling = true,
    healthEndpoint = '/health',
    timeout = 5000,
  } = options;

  const [status, setStatus] = useState<BackendHealthStatus>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [responseTime, setResponseTime] = useState<number | null>(null);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Check backend health status
   */
  const checkHealth = useCallback(async () => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    const startTime = performance.now();

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8009';
      const url = `${apiUrl}${healthEndpoint}`;

      logger.debug('Checking backend health', { url });

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: abortControllerRef.current.signal,
        // Add timeout using AbortSignal.timeout (modern browsers)
        ...(AbortSignal.timeout ? { signal: AbortSignal.timeout(timeout) } : {}),
      });

      const endTime = performance.now();
      const responseTimeMs = Math.round(endTime - startTime);

      if (response.ok) {
        setStatus('online');
        setError(null);
        setResponseTime(responseTimeMs);
        setLastChecked(new Date());

        logger.info('Backend health check succeeded', {
          responseTime: `${responseTimeMs}ms`,
          status: response.status,
        });
      } else {
        throw new Error(`Health check failed with status ${response.status}`);
      }
    } catch (err: any) {
      // Ignore aborted requests
      if (err.name === 'AbortError') {
        logger.debug('Health check aborted');
        return;
      }

      const endTime = performance.now();
      const responseTimeMs = Math.round(endTime - startTime);

      setStatus('offline');
      setResponseTime(responseTimeMs);
      setLastChecked(new Date());

      // Determine error message
      let errorMessage = 'Backend unreachable';
      if (err.message?.includes('fetch')) {
        errorMessage = 'Network error - backend unreachable';
      } else if (err.message?.includes('timeout')) {
        errorMessage = 'Request timeout - backend slow or unavailable';
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);

      logger.warn('Backend health check failed', {
        error: errorMessage,
        responseTime: `${responseTimeMs}ms`,
      });
    }
  }, [healthEndpoint, timeout]);

  /**
   * Setup polling interval
   */
  useEffect(() => {
    // Initial check
    checkHealth();

    // Setup polling if enabled
    if (enablePolling && pollInterval > 0) {
      pollIntervalRef.current = setInterval(() => {
        checkHealth();
      }, pollInterval);

      logger.info('Backend health polling started', {
        interval: `${pollInterval}ms`,
      });
    }

    // Cleanup
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        logger.info('Backend health polling stopped');
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [checkHealth, enablePolling, pollInterval]);

  /**
   * Check health when tab becomes visible again
   */
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        logger.debug('Tab became visible, checking backend health');
        checkHealth();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [checkHealth]);

  return {
    status,
    lastChecked,
    error,
    responseTime,
    checkHealth,
  };
}

export default useBackendHealth;
