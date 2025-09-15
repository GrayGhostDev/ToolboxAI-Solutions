/**
 * Auth Sync Configuration
 *
 * Manages dual-mode operation for testing and production
 * Uses environment variables to determine operating mode
 */

// Environment mode detection
export const AUTH_MODE = {
  IS_TEST: import.meta.env.MODE === 'test' || import.meta.env.VITE_AUTH_MODE === 'test',
  IS_MOCK: import.meta.env.VITE_USE_MOCK_AUTH === 'true',
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
};

// Feature flags for auth functionality
export const AUTH_FEATURES = {
  ENABLE_AUTO_REFRESH: !AUTH_MODE.IS_TEST && import.meta.env.VITE_ENABLE_AUTO_REFRESH !== 'false',
  ENABLE_SESSION_MONITORING: !AUTH_MODE.IS_TEST && import.meta.env.VITE_ENABLE_SESSION_MONITORING !== 'false',
  ENABLE_CROSS_TAB_SYNC: !AUTH_MODE.IS_TEST && import.meta.env.VITE_ENABLE_CROSS_TAB_SYNC !== 'false',
  ENABLE_RETRY_LOGIC: import.meta.env.VITE_ENABLE_RETRY_LOGIC !== 'false',
  ENABLE_ERROR_RECOVERY: import.meta.env.VITE_ENABLE_ERROR_RECOVERY !== 'false',
};

// Timing configurations (can be overridden by environment variables)
export const AUTH_TIMING = {
  TOKEN_REFRESH_THRESHOLD: parseInt(import.meta.env.VITE_TOKEN_REFRESH_THRESHOLD || '5'), // minutes
  SESSION_TIMEOUT: parseInt(import.meta.env.VITE_SESSION_TIMEOUT || '30'), // minutes
  INACTIVITY_WARNING: parseInt(import.meta.env.VITE_INACTIVITY_WARNING || '25'), // minutes
  MAX_RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_MAX_RETRY_ATTEMPTS || '3'),
  RETRY_DELAYS: [1000, 3000, 5000], // milliseconds
};

// API endpoints (can be mocked or real)
export const AUTH_ENDPOINTS = {
  REFRESH: AUTH_MODE.IS_MOCK ? '/mock/auth/refresh' : '/auth/refresh',
  LOGOUT: AUTH_MODE.IS_MOCK ? '/mock/auth/logout' : '/auth/logout',
  USER_INFO: AUTH_MODE.IS_MOCK ? '/mock/api/v1/users/me' : '/api/v1/users/me',
};

/**
 * Fetch wrapper that can use mock or real implementation
 */
export class FetchWrapper {
  private static realFetch = typeof window !== 'undefined' ? window.fetch.bind(window) : fetch;
  private static mockFetch: typeof fetch | null = null;
  private static mockResponses: Map<string, any> = new Map();

  /**
   * Configure mock responses for testing
   */
  static configureMock(mockFn?: typeof fetch) {
    if (mockFn) {
      this.mockFetch = mockFn;
    }
  }

  /**
   * Add a mock response for a specific URL pattern
   */
  static addMockResponse(urlPattern: string | RegExp, response: any) {
    const key = urlPattern instanceof RegExp ? urlPattern.source : urlPattern;
    this.mockResponses.set(key, response);
  }

  /**
   * Clear all mock responses
   */
  static clearMocks() {
    this.mockResponses.clear();
    this.mockFetch = null;
  }

  /**
   * Get the appropriate fetch function based on mode
   */
  static getFetch(): typeof fetch {
    // In test mode, use mock if available
    if (AUTH_MODE.IS_TEST && this.mockFetch) {
      return this.mockFetch;
    }

    // In mock mode, use our mock implementation
    if (AUTH_MODE.IS_MOCK) {
      return this.createMockFetch();
    }

    // Otherwise use real fetch
    return this.realFetch;
  }

  /**
   * Create a mock fetch implementation
   */
  private static createMockFetch(): typeof fetch {
    return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = input.toString();

      // Check for matching mock response
      for (const [pattern, response] of this.mockResponses) {
        const regex = new RegExp(pattern);
        if (regex.test(url)) {
          // Simulate network delay
          await new Promise(resolve => setTimeout(resolve, 100));

          if (response instanceof Error) {
            throw response;
          }

          return new Response(JSON.stringify(response.body), {
            status: response.status || 200,
            headers: new Headers({
              'Content-Type': 'application/json',
              ...response.headers,
            }),
          });
        }
      }

      // Default mock responses
      if (url.includes('/auth/refresh')) {
        return new Response(JSON.stringify({
          access_token: 'mock-access-token-' + Date.now(),
          refresh_token: 'mock-refresh-token-' + Date.now(),
          user: {
            id: 'mock-user-123',
            email: 'mock@example.com',
            role: 'teacher',
          },
        }), { status: 200 });
      }

      if (url.includes('/auth/logout')) {
        return new Response(JSON.stringify({ success: true }), { status: 200 });
      }

      if (url.includes('/users/me')) {
        return new Response(JSON.stringify({
          id: 'mock-user-123',
          email: 'mock@example.com',
          display_name: 'Mock User',
          role: 'teacher',
        }), { status: 200 });
      }

      // Fallback to real fetch for unmocked URLs
      return this.realFetch(input, init);
    };
  }

  /**
   * Perform fetch with automatic mode selection
   */
  static async fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const fetchFn = this.getFetch();

    // Add debug logging in development
    if (AUTH_MODE.IS_DEVELOPMENT && !AUTH_MODE.IS_TEST) {
      console.log(`[Auth Fetch] ${AUTH_MODE.IS_MOCK ? 'MOCK' : 'REAL'} - ${input}`);
    }

    return fetchFn(input, init);
  }
}

/**
 * LocalStorage wrapper for dual-mode operation
 */
export class StorageWrapper {
  private static mockStorage: Map<string, string> = new Map();
  private static useMock: boolean = AUTH_MODE.IS_TEST || AUTH_MODE.IS_MOCK;

  /**
   * Enable or disable mock storage
   */
  static setMockMode(enabled: boolean) {
    this.useMock = enabled;
  }

  /**
   * Get item from storage
   */
  static getItem(key: string): string | null {
    if (this.useMock) {
      return this.mockStorage.get(key) || null;
    }
    return localStorage.getItem(key);
  }

  /**
   * Set item in storage
   */
  static setItem(key: string, value: string): void {
    if (this.useMock) {
      this.mockStorage.set(key, value);
    } else {
      localStorage.setItem(key, value);
    }
  }

  /**
   * Remove item from storage
   */
  static removeItem(key: string): void {
    if (this.useMock) {
      this.mockStorage.delete(key);
    } else {
      localStorage.removeItem(key);
    }
  }

  /**
   * Clear all storage
   */
  static clear(): void {
    if (this.useMock) {
      this.mockStorage.clear();
    } else {
      localStorage.clear();
    }
  }

  /**
   * Get all keys (for testing)
   */
  static getAllKeys(): string[] {
    if (this.useMock) {
      return Array.from(this.mockStorage.keys());
    }
    return Object.keys(localStorage);
  }

  /**
   * Reset mock storage
   */
  static resetMock(): void {
    this.mockStorage.clear();
  }
}

/**
 * BroadcastChannel wrapper for dual-mode operation
 */
export class BroadcastWrapper {
  private static mockChannels: Map<string, Set<(data: any) => void>> = new Map();
  private static realChannels: Map<string, BroadcastChannel> = new Map();

  /**
   * Create or get a channel
   */
  static getChannel(name: string): {
    postMessage: (data: any) => void;
    onmessage: ((event: MessageEvent) => void) | null;
    close: () => void;
  } {
    // In test or mock mode, use mock implementation
    if (AUTH_MODE.IS_TEST || AUTH_MODE.IS_MOCK) {
      return this.getMockChannel(name);
    }

    // In production, use real BroadcastChannel if available
    if (typeof BroadcastChannel !== 'undefined') {
      if (!this.realChannels.has(name)) {
        this.realChannels.set(name, new BroadcastChannel(name));
      }
      return this.realChannels.get(name)!;
    }

    // Fallback to mock if BroadcastChannel not available
    return this.getMockChannel(name);
  }

  /**
   * Get mock channel implementation
   */
  private static getMockChannel(name: string) {
    if (!this.mockChannels.has(name)) {
      this.mockChannels.set(name, new Set());
    }

    const listeners = this.mockChannels.get(name)!;
    let messageHandler: ((event: MessageEvent) => void) | null = null;

    return {
      postMessage: (data: any) => {
        // Simulate async message delivery
        setTimeout(() => {
          listeners.forEach(listener => listener(data));
        }, 0);
      },
      set onmessage(handler: ((event: MessageEvent) => void) | null) {
        if (messageHandler) {
          listeners.delete(messageHandler);
        }
        messageHandler = handler;
        if (handler) {
          const wrapper = (data: any) => handler({ data } as MessageEvent);
          listeners.add(wrapper);
        }
      },
      get onmessage() {
        return messageHandler;
      },
      close: () => {
        if (messageHandler) {
          listeners.delete(messageHandler);
        }
      },
    };
  }

  /**
   * Clear all channels (for testing)
   */
  static clearAll(): void {
    this.mockChannels.clear();
    this.realChannels.forEach(channel => channel.close());
    this.realChannels.clear();
  }
}

/**
 * Timer wrapper for testing
 */
export class TimerWrapper {
  private static useMock: boolean = AUTH_MODE.IS_TEST;
  private static timers: Set<NodeJS.Timeout> = new Set();

  /**
   * Set mock mode
   */
  static setMockMode(enabled: boolean) {
    this.useMock = enabled;
  }

  /**
   * Set timeout with tracking
   */
  static setTimeout(callback: () => void, ms: number): NodeJS.Timeout {
    const timer = setTimeout(() => {
      this.timers.delete(timer);
      callback();
    }, ms);
    this.timers.add(timer);
    return timer;
  }

  /**
   * Clear timeout
   */
  static clearTimeout(timer: NodeJS.Timeout): void {
    clearTimeout(timer);
    this.timers.delete(timer);
  }

  /**
   * Set interval with tracking
   */
  static setInterval(callback: () => void, ms: number): NodeJS.Timeout {
    const timer = setInterval(callback, ms);
    this.timers.add(timer);
    return timer;
  }

  /**
   * Clear interval
   */
  static clearInterval(timer: NodeJS.Timeout): void {
    clearInterval(timer);
    this.timers.delete(timer);
  }

  /**
   * Clear all timers (for testing cleanup)
   */
  static clearAll(): void {
    this.timers.forEach(timer => {
      clearTimeout(timer);
      clearInterval(timer);
    });
    this.timers.clear();
  }
}

/**
 * Get auth configuration based on environment
 */
export function getAuthConfig() {
  return {
    tokenRefreshThreshold: AUTH_TIMING.TOKEN_REFRESH_THRESHOLD,
    sessionTimeout: AUTH_TIMING.SESSION_TIMEOUT,
    inactivityWarning: AUTH_TIMING.INACTIVITY_WARNING,
    enableAutoRefresh: AUTH_FEATURES.ENABLE_AUTO_REFRESH,
    enableSessionMonitoring: AUTH_FEATURES.ENABLE_SESSION_MONITORING,
    syncWithBackend: !AUTH_MODE.IS_MOCK,
  };
}

/**
 * Reset all mocks (for testing)
 */
export function resetAllMocks() {
  FetchWrapper.clearMocks();
  StorageWrapper.resetMock();
  BroadcastWrapper.clearAll();
  TimerWrapper.clearAll();
}

// Export mode information for debugging
export const AUTH_ENV_INFO = {
  mode: AUTH_MODE,
  features: AUTH_FEATURES,
  timing: AUTH_TIMING,
  endpoints: AUTH_ENDPOINTS,
};

// Log configuration in development (but not in tests)
if (AUTH_MODE.IS_DEVELOPMENT && !AUTH_MODE.IS_TEST) {
  console.log('🔐 Auth Configuration:', AUTH_ENV_INFO);
}