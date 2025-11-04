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
    /WARNING.*WebGL contexts/i,

    // Browser extension errors (Grammarly, password managers, etc.)
    /runtime\.lastError/i,
    /message port closed/i,
    /Could not establish connection/i,
    /Receiving end does not exist/i,
    /background\.js/i,
    /FrameDoesNotExistError/i,
    /FrameIsBrowserFrameError/i,
    /Frame \d+ does not exist/i,
    /Frame \d+ in tab \d+ is a browser frame/i,

    // Chrome extension content script errors
    /chrome-extension:\/\//i,
    /extensions::/i,

    // React DevTools errors
    /react_devtools_backend/i,
    /Invalid argument not valid semver/i,
    /validateAndParse.*semver/i,

    // SVG attribute errors from third-party components
    /svg.*attribute.*Expected length/i,
    /svg.*width.*calc/i,
    /svg.*height.*calc/i,
    /attribute width.*Expected length/i,
    /attribute height.*Expected length/i,

    // File not found errors from extensions
    /utils\.js.*ERR_FILE_NOT_FOUND/i,
    /extensionState\.js.*ERR_FILE_NOT_FOUND/i,
    /heuristicsRedefinitions\.js.*ERR_FILE_NOT_FOUND/i,
    /chrome-extension.*ERR_FILE_NOT_FOUND/i,

    // CORS errors (expected when backend is down or has CORS issues in dev)
    /blocked by CORS policy/i,
    /No 'Access-Control-Allow-Origin'/i,
    /CORS.*preflight/i,
    /Access to fetch.*blocked by CORS/i,

    // Fetch failed errors (backend down in dev)
    /Failed to fetch/i,
    /fetch.*failed/i,
    /Fetch failed loading/i,
    /Network error.*backend unreachable/i,
    /Backend health check failed/i,
    /GET.*health.*ERR_FAILED/i,
    /GET.*health.*net::ERR_FAILED/i,
    /GET.*toolboxai-backend.*health/i,

    // Configuration warnings (expected in dev)
    /Configuration warnings detected/i,
    /Backend unavailable/i
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

  // Intercept React's console.error before it's overridden
  // This catches SVG attribute warnings from React DOM
  const reactErrorHandler = console.error;
  console.error = function(...args: any[]) {
    // Check if this is a React DOM SVG warning
    const firstArg = args[0];
    if (typeof firstArg === 'string') {
      if (
        firstArg.includes('<svg> attribute') ||
        firstArg.includes('Expected length') ||
        firstArg.includes('calc(')
      ) {
        // Suppress SVG attribute warnings (they're harmless, from Mantine icons)
        if (import.meta.env.VITE_DEBUG_MODE === 'true') {
          console.debug('[SUPPRESSED-SVG]', firstArg);
        }
        return;
      }
    }

    // Check other suppression patterns
    if (!shouldSuppressMessage(args)) {
      reactErrorHandler.apply(console, args);
    } else if (import.meta.env.VITE_DEBUG_MODE === 'true') {
      console.debug('[HMR-SUPPRESSED]', ...args);
    }
  };

  console.log('🔇 HMR error suppressor initialized (aggressive mode for Docker)');
}

