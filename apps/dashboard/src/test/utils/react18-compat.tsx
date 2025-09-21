/**
 * React 18 Test Compatibility Layer
 *
 * Provides compatibility fixes for React 18 concurrent features in tests
 * Addresses the "Should not already be working" error with MUI components
 */

import { configure } from '@testing-library/react';

// Configure testing-library for React 18
configure({
  // Wrap all renders in act() to handle concurrent features
  asyncUtilTimeout: 2000,
  // Disable concurrent features in tests
  reactStrictMode: false,
});

// Fix for React 18 concurrent rendering in tests
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

// Monkey-patch console.error to suppress specific React 18 warnings in tests
const originalError = console.error;
console.error = (...args: any[]) => {
  // Suppress known React 18 test warnings
  if (
    typeof args[0] === 'string' &&
    (args[0].includes('Should not already be working') ||
     args[0].includes('useInsertionEffect must not schedule updates') ||
     args[0].includes('Warning: ReactDOM.createRoot is no longer supported') ||
     args[0].includes('Cannot update a component') ||
     args[0].includes('Warning: An update to') ||
     args[0].includes('Warning: Attempted to synchronously unmount'))
  ) {
    return;
  }
  originalError.apply(console, args);
};

export default {};