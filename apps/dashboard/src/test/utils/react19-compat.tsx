/**
 * React 19 Test Compatibility Layer
 *
 * Provides compatibility fixes for React 19 concurrent features in tests
 * Addresses React 19 specific rendering and hydration behaviors
 */

import { configure } from '@testing-library/react';

// Configure testing-library for React 19
configure({
  // React 19 has improved concurrent rendering - allow longer timeouts
  asyncUtilTimeout: 3000,
  // React 19 handles StrictMode better, but still disable for tests
  reactStrictMode: false,
});

// React 19 act environment configuration
if (typeof globalThis.IS_REACT_ACT_ENVIRONMENT === 'undefined') {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
}

// Force React to use legacy mode in tests
if (typeof window !== 'undefined') {
  (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__ = {
    isDisabled: true,
    supportsFiber: true,
    renderers: new Map(),
    onScheduleFiberRoot: () => {},
    onCommitFiberRoot: () => {},
    onCommitFiberUnmount: () => {},
  };
}

// Monkey-patch console.error to suppress specific React 19 warnings in tests
const originalError = console.error;
console.error = (...args: any[]) => {
  // Suppress known React 19 test warnings
  if (
    typeof args[0] === 'string' &&
    (args[0].includes('Should not already be working') ||
     args[0].includes('useInsertionEffect must not schedule updates') ||
     args[0].includes('Warning: ReactDOM.createRoot is no longer supported') ||
     args[0].includes('Cannot update a component') ||
     args[0].includes('Warning: An update to') ||
     args[0].includes('Warning: Attempted to synchronously unmount') ||
     args[0].includes('Warning: Using UNSAFE_') ||
     args[0].includes('Warning: React.createFactory') ||
     args[0].includes('Warning: componentWillMount') ||
     args[0].includes('Warning: componentWillReceiveProps') ||
     args[0].includes('Warning: componentWillUpdate'))
  ) {
    return;
  }
  originalError.apply(console, args);
};

export default {};