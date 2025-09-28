import '@testing-library/jest-dom';
import { vi, beforeAll, afterAll } from 'vitest';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
global.localStorage = localStorageMock as Storage;

// Fix for DataCloneError with axios in Vitest
// Override structuredClone to handle non-serializable objects
if (typeof structuredClone === 'undefined') {
  global.structuredClone = (obj: unknown) => {
    return JSON.parse(JSON.stringify(obj));
  };
} else {
  // Override existing structuredClone to handle axios config objects
  const originalStructuredClone = global.structuredClone;
  global.structuredClone = (obj: unknown, options?: unknown) => {
    try {
      // Try the original first
      return originalStructuredClone(obj, options);
    } catch (_e) {
      // If it fails (e.g., with functions), fallback to JSON serialization
      // This removes functions but preserves data structure
      const serializable = JSON.parse(JSON.stringify(obj, (key, value) => {
        if (typeof value === 'function') {
          return undefined; // Remove functions
        }
        return value;
      }));
      return serializable;
    }
  };
}

// Mock WebSocket
class WebSocketMock {
  constructor(public url: string) {}
  send = vi.fn();
  close = vi.fn();
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
}
global.WebSocket = WebSocketMock as unknown as typeof WebSocket;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Suppress console errors in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
       args[0].includes('Warning: useLayoutEffect') ||
       args[0].includes('Not implemented: navigation'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
