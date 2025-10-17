/**
 * Console Filter Utility
 *
 * Filters out known non-critical warnings from the console
 * Primarily used to suppress React 19 + Mantine compatibility warnings
 */

const originalWarn = console.warn;
const originalError = console.error;

// List of warning patterns to suppress
const SUPPRESS_PATTERNS = [
  // React 19 + Mantine prop warnings
  /React does not recognize the `(justifyContent|alignItems|flexWrap|scrollButtons|gutterBottom|fullWidth|InputProps)` prop on a DOM element/,
  // React DevTools semver warnings (browser extension issue)
  /Invalid argument not valid semver/,
];

/**
 * Check if a message should be suppressed
 */
function shouldSuppress(args: any[]): boolean {
  const message = args.join(' ');
  return SUPPRESS_PATTERNS.some(pattern => pattern.test(message));
}

/**
 * Initialize console filtering for development mode
 */
export function initConsoleFilter() {
  // Only apply in development mode
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  // Override console.warn
  console.warn = (...args: any[]) => {
    if (!shouldSuppress(args)) {
      originalWarn.apply(console, args);
    }
  };

  // Override console.error
  console.error = (...args: any[]) => {
    if (!shouldSuppress(args)) {
      originalError.apply(console, args);
    }
  };
}

/**
 * Restore original console methods
 */
export function restoreConsole() {
  console.warn = originalWarn;
  console.error = originalError;
}
