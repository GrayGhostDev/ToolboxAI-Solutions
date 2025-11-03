/**
 * ============================================
 * SENTRY CONFIGURATION - FRONTEND
 * ============================================
 * Sentry monitoring and error tracking setup
 * Updated: 2025-11-02
 * ============================================
 */

import * as Sentry from '@sentry/react';

/**
 * Initialize Sentry for error tracking and performance monitoring
 */
export const initSentry = () => {
  // Only initialize in production
  if (import.meta.env.PROD) {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      environment: import.meta.env.VITE_ENVIRONMENT || 'production',
      release: import.meta.env.VITE_COMMIT_SHA || 'unknown',

      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration({
          // Privacy settings
          maskAllText: false,
          blockAllMedia: false,
          // Network recording
          networkDetailAllowUrls: [
            window.location.origin,
            /https:\/\/.*\.onrender\.com/,
            /https:\/\/.*\.supabase\.co/,
          ],
        }),
      ],

      // Performance Monitoring
      tracesSampleRate: import.meta.env.DEV ? 1.0 : 0.1, // 10% in production

      // Session Replay
      replaysSessionSampleRate: 0.1, // 10% of sessions
      replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors

      // Before sending events
      beforeSend(event, hint) {
        // Filter out sensitive data
        if (event.request?.headers) {
          delete event.request.headers.Authorization;
          delete event.request.headers['X-API-Key'];
          delete event.request.headers.Cookie;
        }

        // Filter out specific errors
        const error = hint.originalException;
        if (error && typeof error === 'object' && 'message' in error) {
          const message = String(error.message);

          // Ignore network errors
          if (message.includes('NetworkError') || message.includes('Failed to fetch')) {
            return null;
          }

          // Ignore cancelled requests
          if (message.includes('AbortError') || message.includes('cancelled')) {
            return null;
          }
        }

        return event;
      },

      // Ignore specific errors
      ignoreErrors: [
        // Browser extensions
        'top.GLOBALS',
        'chrome-extension://',
        'moz-extension://',
        // Network issues
        'NetworkError',
        'Failed to fetch',
        'Load failed',
        // User cancellations
        'AbortError',
        'Request aborted',
      ],

      // Deny URLs
      denyUrls: [
        /extensions\//i,
        /^chrome:\/\//i,
        /^moz-extension:\/\//i,
      ],
    });

    console.log('✅ Sentry initialized for production monitoring');
  } else {
    console.log('ℹ️ Sentry disabled in development mode');
  }
};

/**
 * Set user context for Sentry
 */
export const setSentryUser = (user: {
  id: string;
  email?: string;
  username?: string;
}) => {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
  });
};

/**
 * Clear user context
 */
export const clearSentryUser = () => {
  Sentry.setUser(null);
};

/**
 * Capture a custom error
 */
export const captureError = (error: Error, context?: Record<string, any>) => {
  if (context) {
    Sentry.setContext('custom', context);
  }
  Sentry.captureException(error);
};

/**
 * Capture a custom message
 */
export const captureMessage = (message: string, level: Sentry.SeverityLevel = 'info') => {
  Sentry.captureMessage(message, level);
};

/**
 * Add breadcrumb for debugging
 */
export const addBreadcrumb = (breadcrumb: Sentry.Breadcrumb) => {
  Sentry.addBreadcrumb(breadcrumb);
};

export { Sentry };

