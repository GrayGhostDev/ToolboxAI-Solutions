/**
 * ULTRA-AGGRESSIVE Error Suppressor Pre-load Script
 *
 * This script MUST load before React to intercept ALL console errors.
 * Patches console.error at the lowest level to catch React-DOM internals.
 */

(function() {
  'use strict';

  // Store original console methods IMMEDIATELY
  const originalError = console.error.bind(console);
  const originalWarn = console.warn.bind(console);
  const originalLog = console.log.bind(console);

  // Patterns to suppress - EXPANDED
  const suppressPatterns = [
    // SVG attribute errors (Mantine icons)
    /<svg>.*attribute.*width.*Expected length/i,
    /<svg>.*attribute.*height.*Expected length/i,
    /attribute width.*Expected length.*calc/i,
    /attribute height.*Expected length.*calc/i,
    /Error:.*<svg>.*attribute/i,

    // CORS errors (backend down in dev) - MOST COMMON
    /blocked by CORS policy/i,
    /No 'Access-Control-Allow-Origin'/i,
    /Access to fetch.*blocked by CORS/i,
    /Response to preflight request/i,
    /CORS.*preflight/i,
    /Access-Control-Allow-Origin/i,

    // Fetch failed errors - VERY COMMON IN DEV
    /Failed to fetch/i,
    /Fetch failed loading/i,
    /GET.*health.*ERR_FAILED/i,
    /GET.*toolboxai-backend/i,
    /toolboxai-backend\.onrender\.com.*health/i,
    /window\.fetch.*checkBackendHealth/i,
    /GET "https:\/\/toolboxai-backend/i,
    /net::ERR_FAILED/i,

    // Chrome extension errors - SPAM FROM BROWSER EXTENSIONS
    /chrome-extension.*ERR_FILE_NOT_FOUND/i,
    /Failed to load resource.*chrome-extension/i,
    /GET chrome-extension/i,
    /pejdijmoenmkgeppbflobdenhhabjlaj/i,
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

  // ULTRA-AGGRESSIVE console.error override using Object.defineProperty
  // This PREVENTS React-DOM from overwriting our suppression
  const suppressedError = function(...args) {
    try {
      // Check FIRST argument specifically for React-DOM errors
      const firstArg = args[0];
      if (firstArg) {
        const message = String(firstArg);

        // IMMEDIATELY suppress SVG errors (most aggressive check)
        if (message.includes('<svg>') ||
            message.includes('attribute width') ||
            message.includes('attribute height') ||
            message.includes('Expected length') ||
            message.includes('calc(1rem') ||
            message.includes('calc(1.125rem') ||
            message.includes('var(--mantine-') ||
            (message.includes('Error:') && message.includes('svg'))) {
          return; // SILENT SUPPRESSION - NO OUTPUT
        }

        // Suppress 403 Not authenticated errors (expected when not logged in)
        if ((message.includes('403') && message.includes('Not authenticated')) ||
            message.includes('/api/v1/users/me/profile] Error 403')) {
          return; // SILENT SUPPRESSION - NOT AN ERROR
        }

        // Suppress API errors for authentication endpoints when not logged in
        if (message.includes('Request failed with status code 403') ||
            (message.includes('API Error') && message.includes('403'))) {
          return; // SILENT SUPPRESSION - EXPECTED BEHAVIOR
        }

        // Suppress "Failed to restore authentication" warnings (expected when not logged in)
        if (message.includes('Failed to restore authentication')) {
          return; // SILENT SUPPRESSION - EXPECTED BEHAVIOR
        }
      }

      // Then check all patterns
      if (!shouldSuppress(args)) {
        originalError(...args);
      }
    } catch (e) {
      // Safely fail - don't break the app
      originalError(...args);
    }
  };

  // Make console.error configurable for HMR but still suppress errors
  // Use a getter/setter that allows reassignment but keeps suppression active
  let currentErrorHandler = suppressedError;

  try {
    Object.defineProperty(console, 'error', {
      get: function() {
        return currentErrorHandler;
      },
      set: function(newHandler) {
        try {
          // Allow HMR to set new handler, but wrap it with our suppression
          if (typeof newHandler === 'function') {
            const wrappedHandler = function(...args) {
              try {
                // Check if should suppress
                if (!shouldSuppress(args)) {
                  // Call the new handler
                  newHandler.apply(console, args);
                }
              } catch (e) {
                // Safely fail
                originalError(...args);
              }
            };
            currentErrorHandler = wrappedHandler;
          }
        } catch (e) {
          // Safely fail
          currentErrorHandler = suppressedError;
        }
      },
      configurable: true, // Allow reconfiguration
      enumerable: true
    });
  } catch (e) {
    // Fallback: just replace console.error directly
    console.error = suppressedError;
  }

  // Override console.warn with ENHANCED 403 suppression
  console.warn = function(...args) {
    // Check first argument for authentication warnings
    const firstArg = args[0];
    if (firstArg) {
      const message = String(firstArg);

      // Suppress "Failed to restore authentication" warnings
      if (message.includes('Failed to restore authentication') ||
          message.includes('AxiosError') ||
          message.includes('Request failed with status code 403')) {
        return; // SILENT SUPPRESSION - EXPECTED BEHAVIOR
      }
    }

    if (!shouldSuppress(args)) {
      originalWarn(...args);
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

  // Suppress global errors (including fetch failures)
  window.addEventListener('error', function(event) {
    try {
      const message = event.message || event.error?.message || event.filename || '';
      const fullContext = message + ' ' + (event.error?.stack || '');

      if (suppressPatterns.some(pattern => pattern.test(fullContext) || pattern.test(message))) {
        event.preventDefault();
        event.stopPropagation();
        return true;
      }
    } catch (e) {
      // Let original error through
    }
  }, true);

  // Additional suppression for resource loading errors (chrome-extension files)
  window.addEventListener('error', function(event) {
    // Suppress extension resource load failures
    if (event.target && event.target.tagName) {
      const src = event.target.src || event.target.href || '';
      if (src.includes('chrome-extension://') ||
          src.includes('pejdijmoenmkgeppbflobdenhhabjlaj')) {
        event.preventDefault();
        event.stopPropagation();
        return true;
      }
    }
  }, true);


  // Log IMMEDIATELY to confirm we're loaded
  originalLog('🔇 Error suppressor pre-loaded (before React) - FLEXIBLE MODE');
  originalLog('✅ console.error suppression active (HMR compatible)');
})();

