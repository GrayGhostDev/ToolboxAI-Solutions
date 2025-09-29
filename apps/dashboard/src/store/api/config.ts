/**
 * RTK Query Configuration and Performance Optimization
 *
 * This file centralizes RTK Query configuration including:
 * - Cache timing and invalidation strategies
 * - Request deduplication settings
 * - Background refetching policies
 * - Error handling and retry logic
 * - Performance monitoring
 */

import { SerializedError } from '@reduxjs/toolkit';
import { FetchBaseQueryError } from '@reduxjs/toolkit/query';

// Cache configuration constants
export const CACHE_CONFIG = {
  // Default cache times (in seconds)
  KEEP_UNUSED_DATA_FOR: 300, // 5 minutes
  REFETCH_ON_MOUNT_OR_ARG_CHANGE: 300, // Refetch if data is older than 5 minutes

  // Polling intervals (in milliseconds)
  POLLING: {
    DASHBOARD: 30000,      // 30 seconds
    MESSAGES: 60000,       // 1 minute
    CLASSES: 120000,       // 2 minutes
    ASSESSMENTS: 180000,   // 3 minutes
    ANALYTICS: 300000,     // 5 minutes
    REAL_TIME: 5000,       // 5 seconds for real-time data
  },

  // Cache invalidation rules
  INVALIDATION: {
    // Tags that should be invalidated together
    RELATED_TAGS: {
      'Class': ['Dashboard', 'Analytics'],
      'Lesson': ['Class', 'Dashboard'],
      'Assessment': ['Class', 'Lesson', 'Progress'],
      'Message': ['Dashboard'],
      'User': ['Dashboard', 'Class'],
      'Progress': ['Dashboard', 'Analytics'],
    },

    // Time-based invalidation (in milliseconds)
    AUTO_INVALIDATE: {
      'Dashboard': 300000,    // 5 minutes
      'Analytics': 600000,    // 10 minutes
      'Compliance': 3600000,  // 1 hour
    },
  },

  // Request deduplication
  DEDUPLICATION: {
    // Time window for deduplicating identical requests (in milliseconds)
    WINDOW: 1000, // 1 second

    // Skip deduplication for these endpoints
    SKIP_ENDPOINTS: ['triggerRealtime'],
  },
} as const;

// Performance thresholds for monitoring
export const PERFORMANCE_THRESHOLDS = {
  CACHE_HIT_RATIO: {
    EXCELLENT: 0.8,  // 80%+
    GOOD: 0.6,       // 60-79%
    POOR: 0.4,       // Below 40%
  },

  RESPONSE_TIME: {
    FAST: 500,       // Under 500ms
    ACCEPTABLE: 2000, // Under 2s
    SLOW: 5000,      // Over 5s
  },

  ERROR_RATE: {
    EXCELLENT: 0.01, // Under 1%
    ACCEPTABLE: 0.05, // Under 5%
    CONCERNING: 0.1,  // Over 10%
  },
} as const;

// Retry configuration for failed requests
export const RETRY_CONFIG = {
  // Maximum number of retries
  MAX_RETRIES: 3,

  // Base delay between retries (in milliseconds)
  BASE_DELAY: 1000,

  // Exponential backoff multiplier
  BACKOFF_MULTIPLIER: 2,

  // Maximum delay between retries (in milliseconds)
  MAX_DELAY: 30000,

  // HTTP status codes that should trigger retries
  RETRYABLE_STATUS_CODES: [408, 429, 500, 502, 503, 504],

  // Network error types that should trigger retries
  RETRYABLE_ERRORS: ['FETCH_ERROR', 'TIMEOUT_ERROR'],
} as const;

// Smart refetching configuration
export const REFETCH_CONFIG = {
  // Refetch on window focus for these endpoints
  REFETCH_ON_FOCUS: [
    'getDashboardOverview',
    'getMessages',
    'getClasses',
  ],

  // Refetch on network reconnect for these endpoints
  REFETCH_ON_RECONNECT: [
    'getDashboardOverview',
    'getMessages',
    'getClasses',
    'getAssessments',
  ],

  // Background refetching for critical data
  BACKGROUND_REFETCH: {
    'getDashboardOverview': {
      interval: 60000, // 1 minute
      enabled: true,
    },
    'getMessages': {
      interval: 30000, // 30 seconds
      enabled: true,
    },
  },
} as const;

// Error classification and handling
export const ERROR_CONFIG = {
  // Error types and their handling strategies
  ERROR_TYPES: {
    NETWORK: {
      codes: ['FETCH_ERROR', 'TIMEOUT_ERROR'],
      showNotification: true,
      allowRetry: true,
      fallbackData: true,
    },
    AUTH: {
      codes: [401, 403],
      showNotification: true,
      allowRetry: false,
      redirectToLogin: true,
    },
    VALIDATION: {
      codes: [400, 422],
      showNotification: true,
      allowRetry: false,
      showFormErrors: true,
    },
    SERVER: {
      codes: [500, 502, 503, 504],
      showNotification: true,
      allowRetry: true,
      fallbackData: false,
    },
    NOT_FOUND: {
      codes: [404],
      showNotification: false,
      allowRetry: false,
      fallbackData: true,
    },
  },

  // Default error messages
  DEFAULT_MESSAGES: {
    NETWORK: 'Unable to connect to the server. Please check your internet connection.',
    AUTH: 'Authentication required. Please log in again.',
    VALIDATION: 'Please check your input and try again.',
    SERVER: 'Server error. Our team has been notified.',
    NOT_FOUND: 'The requested resource was not found.',
    GENERIC: 'An unexpected error occurred. Please try again.',
  },
} as const;

// Feature flags for RTK Query features
export const FEATURE_FLAGS = {
  // Enable optimistic updates
  OPTIMISTIC_UPDATES: true,

  // Enable automatic cache invalidation
  AUTO_CACHE_INVALIDATION: true,

  // Enable performance monitoring
  PERFORMANCE_MONITORING: true,

  // Enable debug logging in development
  DEBUG_LOGGING: process.env.NODE_ENV === 'development',

  // Enable offline support
  OFFLINE_SUPPORT: false, // TODO: Implement offline support

  // Enable request batching
  REQUEST_BATCHING: false, // TODO: Implement request batching

  // Enable data normalization
  DATA_NORMALIZATION: true,
} as const;

// Utility functions for error handling
export function isRetryableError(error: FetchBaseQueryError | SerializedError): boolean {
  if ('status' in error) {
    return RETRY_CONFIG.RETRYABLE_STATUS_CODES.includes(error.status as number);
  }

  if ('name' in error && error.name) {
    return RETRY_CONFIG.RETRYABLE_ERRORS.includes(error.name as typeof RETRY_CONFIG.RETRYABLE_ERRORS[number]);
  }

  return false;
}

export function getErrorType(error: FetchBaseQueryError | SerializedError): keyof typeof ERROR_CONFIG.ERROR_TYPES {
  if ('status' in error) {
    const status = error.status as number;

    for (const [type, config] of Object.entries(ERROR_CONFIG.ERROR_TYPES)) {
      if (config.codes.includes(status)) {
        return type as keyof typeof ERROR_CONFIG.ERROR_TYPES;
      }
    }
  }

  if ('name' in error && error.name) {
    for (const [type, config] of Object.entries(ERROR_CONFIG.ERROR_TYPES)) {
      if (config.codes.includes(error.name)) {
        return type as keyof typeof ERROR_CONFIG.ERROR_TYPES;
      }
    }
  }

  return 'SERVER';
}

export function getErrorMessage(error: FetchBaseQueryError | SerializedError): string {
  const errorType = getErrorType(error);

  // Try to extract specific error message
  if ('data' in error && error.data && typeof error.data === 'object') {
    const data = error.data as any;
    if (data.message) return data.message;
    if (data.detail) {
      if (Array.isArray(data.detail)) {
        return data.detail.map((err: any) => err.msg || err.message || 'Validation error').join(', ');
      }
      if (typeof data.detail === 'string') return data.detail;
    }
    if (data.error) return data.error;
  }

  // Fall back to default message
  return ERROR_CONFIG.DEFAULT_MESSAGES[errorType] || ERROR_CONFIG.DEFAULT_MESSAGES.GENERIC;
}

// Performance monitoring utilities
export function calculateCacheHitRatio(queries: Record<string, any>): number {
  const totalQueries = Object.keys(queries).length;
  if (totalQueries === 0) return 0;

  const successfulQueries = Object.values(queries).filter(
    (query: any) => query.status === 'fulfilled' && !query.error
  ).length;

  return successfulQueries / totalQueries;
}

export function getPerformanceRating(hitRatio: number): 'excellent' | 'good' | 'poor' {
  if (hitRatio >= PERFORMANCE_THRESHOLDS.CACHE_HIT_RATIO.EXCELLENT) return 'excellent';
  if (hitRatio >= PERFORMANCE_THRESHOLDS.CACHE_HIT_RATIO.GOOD) return 'good';
  return 'poor';
}

// Cache management utilities
export function shouldInvalidateRelatedTags(changedTag: string): string[] {
  return CACHE_CONFIG.INVALIDATION.RELATED_TAGS[changedTag] || [];
}

export function getPollingInterval(endpoint: string): number | undefined {
  // Map endpoint names to polling intervals
  if (endpoint.includes('dashboard')) return CACHE_CONFIG.POLLING.DASHBOARD;
  if (endpoint.includes('message')) return CACHE_CONFIG.POLLING.MESSAGES;
  if (endpoint.includes('class')) return CACHE_CONFIG.POLLING.CLASSES;
  if (endpoint.includes('assessment')) return CACHE_CONFIG.POLLING.ASSESSMENTS;
  if (endpoint.includes('analytics')) return CACHE_CONFIG.POLLING.ANALYTICS;

  return undefined; // No polling by default
}

// Development and debugging utilities
export function logCacheState(state: any) {
  if (!FEATURE_FLAGS.DEBUG_LOGGING) return;

  console.group('🔍 RTK Query Cache State');
  console.log('Queries:', Object.keys(state.queries || {}).length);
  console.log('Mutations:', Object.keys(state.mutations || {}).length);
  console.log('Cache hit ratio:', calculateCacheHitRatio(state.queries || {}));
  console.log('Full state:', state);
  console.groupEnd();
}

export function logPerformanceMetrics(metrics: {
  cacheHitRatio: number;
  responseTime: number;
  errorRate: number;
}) {
  if (!FEATURE_FLAGS.DEBUG_LOGGING) return;

  console.group('📊 RTK Query Performance Metrics');
  console.log(`Cache Hit Ratio: ${(metrics.cacheHitRatio * 100).toFixed(1)}% (${getPerformanceRating(metrics.cacheHitRatio)})`);
  console.log(`Avg Response Time: ${metrics.responseTime}ms`);
  console.log(`Error Rate: ${(metrics.errorRate * 100).toFixed(1)}%`);
  console.groupEnd();
}

// Export configuration object for easy import
export const RTK_QUERY_CONFIG = {
  CACHE_CONFIG,
  PERFORMANCE_THRESHOLDS,
  RETRY_CONFIG,
  REFETCH_CONFIG,
  ERROR_CONFIG,
  FEATURE_FLAGS,
} as const;

export default RTK_QUERY_CONFIG;