/**
 * HMR Error Suppressor for Docker Environment
 *
 * This script suppresses non-critical HMR WebSocket errors in development
 * when running in Docker containers where HMR may not work perfectly.
 *
 * The app works fine without HMR - just requires manual browser refresh.
 */

if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  // Store original console methods
  const originalError = console.error;
  const originalWarn = console.warn;

  // Comprehensive list of error patterns to suppress (they're non-critical)
  const suppressPatterns = [
    // WebSocket errors
    /WebSocket closed without opened/i,
    /failed to connect to websocket/i,
    /WebSocket connection.*failed/i,
    /WebSocket.*to.*localhost.*failed/i,

    // Vite HMR errors
    /\[vite].*websocket/i,
    /\[vite].*failed to connect/i,
    /vite.*hmr/i,

    // Generic WebSocket/HMR patterns
    /ws:\/\/localhost:\d+.*failed/i,
    /createConnection.*client:/i,
    /Error.*WebSocket/i,

    // Promise rejection patterns
    /Uncaught.*promise.*WebSocket/i,
    /Unhandled promise rejection.*WebSocket/i,

    // WebGL context warnings (React StrictMode in dev creates duplicates)
    /Too many active WebGL contexts/i,
    /WebGLRenderer.*Context Lost/i,
    /THREE\.WebGLRenderer.*Context/i,
    /WARNING.*WebGL contexts/i
  ];

  // Check if message should be suppressed
  const shouldSuppressMessage = (args: any[]): boolean => {
    try {
      // Convert all arguments to string for checking
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
  };

  // Override console.error to filter HMR WebSocket errors
  console.error = function(...args: any[]) {
    if (!shouldSuppressMessage(args)) {
      originalError.apply(console, args);
    } else if (import.meta.env.VITE_DEBUG_MODE === 'true') {
      console.debug('[HMR-SUPPRESSED]', ...args);
    }
  };

  // Override console.warn for similar patterns
  console.warn = function(...args: any[]) {
    if (!shouldSuppressMessage(args)) {
      originalWarn.apply(console, args);
    } else if (import.meta.env.VITE_DEBUG_MODE === 'true') {
      console.debug('[HMR-SUPPRESSED-WARN]', ...args);
    }
  };

  // Suppress unhandled promise rejections from HMR WebSocket
  window.addEventListener('unhandledrejection', (event) => {
    try {
      const message = event.reason?.message || event.reason?.toString() || '';
      const stack = event.reason?.stack || '';
      const fullMessage = message + ' ' + stack;

      const shouldSuppress = suppressPatterns.some(pattern =>
        pattern.test(fullMessage) || pattern.test(message)
      );

      if (shouldSuppress) {
        event.preventDefault(); // Suppress the error
        if (import.meta.env.VITE_DEBUG_MODE === 'true') {
          console.debug('[HMR-SUPPRESSED-REJECTION]', event.reason);
        }
      }
    } catch (e) {
      // If error checking fails, let the original error through
    }
  }, true); // Use capture phase

  // Also suppress global errors from WebSocket
  window.addEventListener('error', (event) => {
    try {
      const message = event.message || event.error?.message || '';
      const shouldSuppress = suppressPatterns.some(pattern => pattern.test(message));

      if (shouldSuppress) {
        event.preventDefault();
        event.stopPropagation();
        if (import.meta.env.VITE_DEBUG_MODE === 'true') {
          console.debug('[HMR-SUPPRESSED-ERROR]', event.message);
        }
      }
    } catch (e) {
      // If error checking fails, let the original error through
    }
  }, true); // Use capture phase

  console.log('🔇 HMR error suppressor initialized (aggressive mode for Docker)');
}

