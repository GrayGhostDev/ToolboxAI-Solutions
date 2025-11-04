/**
 * Error Suppressor Pre-load Script
 *
 * This script MUST load before React to intercept console errors.
 * Placed in public/ and loaded via <script> tag in index.html.
 */

(function() {
  'use strict';

  // Store original console methods
  const originalError = console.error;
  const originalWarn = console.warn;

  // Patterns to suppress
  const suppressPatterns = [
    // SVG attribute errors (Mantine icons)
    /<svg>.*attribute.*width.*Expected length/i,
    /<svg>.*attribute.*height.*Expected length/i,
    /attribute width.*Expected length.*calc/i,
    /attribute height.*Expected length.*calc/i,

    // CORS errors (backend down in dev)
    /blocked by CORS policy/i,
    /No 'Access-Control-Allow-Origin'/i,
    /Access to fetch.*blocked by CORS/i,

    // Fetch failed errors
    /Failed to fetch/i,
    /Fetch failed loading/i,
    /GET.*health.*ERR_FAILED/i,
    /GET.*toolboxai-backend/i,

    // Chrome extension errors
    /chrome-extension.*ERR_FILE_NOT_FOUND/i,
    /Failed to load resource.*chrome-extension/i,
    /GET chrome-extension/i,
    /utils\.js.*ERR_FILE_NOT_FOUND/i,
    /extensionState\.js.*ERR_FILE_NOT_FOUND/i,
    /heuristicsRedefinitions\.js.*ERR_FILE_NOT_FOUND/i,
    /completion_list\.html/i,

    // Browser extension errors
    /runtime\.lastError/i,
    /message port closed/i,
    /Receiving end does not exist/i,
    /background\.js/i,
  ];

  // Check if message should be suppressed
  function shouldSuppress(args) {
    try {
      const fullMessage = args.map(arg => {
        if (typeof arg === 'string') return arg;
        if (arg?.message) return arg.message;
        if (arg?.stack) return arg.stack;
        return String(arg);
      }).join(' ');

      return suppressPatterns.some(pattern => pattern.test(fullMessage));
    } catch (e) {
      return false;
    }
  }

  // Override console.error
  console.error = function(...args) {
    if (!shouldSuppress(args)) {
      originalError.apply(console, args);
    }
  };

  // Override console.warn
  console.warn = function(...args) {
    if (!shouldSuppress(args)) {
      originalWarn.apply(console, args);
    }
  };

  // Suppress unhandled promise rejections
  window.addEventListener('unhandledrejection', function(event) {
    try {
      const message = event.reason?.message || event.reason?.toString() || '';
      if (suppressPatterns.some(pattern => pattern.test(message))) {
        event.preventDefault();
      }
    } catch (e) {
      // Let original error through
    }
  }, true);

  // Suppress global errors
  window.addEventListener('error', function(event) {
    try {
      const message = event.message || event.error?.message || '';
      if (suppressPatterns.some(pattern => pattern.test(message))) {
        event.preventDefault();
        event.stopPropagation();
        return true;
      }
    } catch (e) {
      // Let original error through
    }
  }, true);

  console.log('🔇 Error suppressor pre-loaded (before React)');
})();

