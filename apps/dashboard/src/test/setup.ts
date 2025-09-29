/**
 * Test Setup for ToolBoxAI Dashboard - 2025 Standards
 *
 * This file configures the test environment with all necessary polyfills,
 * mocks, and utilities for comprehensive testing with Vitest 2.0.
 *
 * @vitest-environment happy-dom
 */

import React from 'react';
import '@testing-library/jest-dom';
import './utils/react19-compat'; // Import React 19 compatibility fixes
import './utils/router-mocks'; // Import router mocks BEFORE any component imports

// CRITICAL: Ensure React is available globally to fix hooks issues
globalThis.React = React;
if (typeof window !== 'undefined') {
  (window as any).React = React;
}

// Additional React setup for test environment
// Ensure React hooks are properly initialized
import { act } from '@testing-library/react';
import ReactDOM from 'react-dom/client';

// Set up React for testing with proper globals
if (typeof globalThis.__REACT_DEVTOOLS_GLOBAL_HOOK__ === 'undefined') {
  globalThis.__REACT_DEVTOOLS_GLOBAL_HOOK__ = {
    isDisabled: true,
    supportsFiber: true,
    renderers: new Map(),
    onScheduleFiberRoot: () => {},
    onCommitFiberRoot: () => {},
    onCommitFiberUnmount: () => {},
  };
}

// Ensure IS_REACT_ACT_ENVIRONMENT is set for React 19
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
import { beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';
import { expect } from 'vitest';
import { TextEncoder, TextDecoder } from 'util';
import { server } from './utils/msw-handlers';

// 2025 Best Practice: Use proper Emotion cache configuration instead of mocking
// See emotion-test-setup.tsx for the proper configuration

// ============================================================================
// CLERK AUTHENTICATION MOCKING
// ============================================================================

// Mock Clerk authentication completely for tests
vi.mock('@clerk/clerk-react', () => {
  return {
    useAuth: vi.fn(() => ({
      isLoaded: true,
      isSignedIn: true,
      userId: 'mock-user-id',
      sessionId: 'mock-session-id',
      getToken: vi.fn(() => Promise.resolve('mock-jwt-token')),
      signOut: vi.fn(() => Promise.resolve())
    })),
    useUser: vi.fn(() => ({
      isLoaded: true,
      isSignedIn: true,
      user: {
        id: 'mock-user-id',
        username: 'test-user',
        firstName: 'Test',
        lastName: 'User',
        imageUrl: 'https://example.com/avatar.png',
        primaryEmailAddress: {
          emailAddress: 'test@example.com',
          verification: { status: 'verified' }
        },
        publicMetadata: { role: 'student' },
        unsafeMetadata: {},
        createdAt: Date.now(),
        update: vi.fn(() => Promise.resolve())
      }
    })),
    useSession: vi.fn(() => ({
      isLoaded: true,
      isSignedIn: true,
      session: {
        id: 'mock-session-id',
        status: 'active',
        user: {
          id: 'mock-user-id',
          username: 'test-user',
          firstName: 'Test',
          lastName: 'User'
        }
      }
    })),
    SignIn: vi.fn(({ children, ...props }) =>
      React.createElement('div', { 'data-testid': 'clerk-sign-in', ...props }, children)
    ),
    SignUp: vi.fn(({ children, ...props }) =>
      React.createElement('div', { 'data-testid': 'clerk-sign-up', ...props }, children)
    ),
    UserButton: vi.fn(({ children, ...props }) =>
      React.createElement('div', { 'data-testid': 'clerk-user-button', ...props }, children)
    ),
    SignOutButton: vi.fn(({ children, ...props }) =>
      React.createElement('button', { 'data-testid': 'clerk-sign-out-button', ...props }, children || 'Sign Out')
    ),
    ClerkProvider: vi.fn(({ children }) => children),
    withClerk: vi.fn((component) => component),
    __esModule: true,
  };
});

// Mock specific MUI transitions that cause DOM issues in happy-dom
vi.mock('@mantine/core', () => ({ Transition: ({ children }: any) => children, () => ({
  default: vi.fn(({ children, in: inProp, timeout, ...props }) => {
    // Return children immediately for testing, ignore transition
    return inProp ? React.createElement('div', { ...props }, children) : null;
  })
}));

vi.mock('@mantine/core', () => ({ Transition: ({ children }: any) => children, () => ({
  default: vi.fn(({ children, in: inProp, timeout, ...props }) => {
    return inProp ? React.createElement('div', { ...props }, children) : null;
  })
}));

vi.mock('@mantine/core', () => ({ Collapse: ({ children }: any) => children, () => ({
  default: vi.fn(({ children, in: inProp, collapsedHeight, timeout, ...props }) => {
    return inProp ? React.createElement('div', { ...props }, children) : null;
  })
}));

// Mock MUI transitions and animations for stable testing
vi.mock('@mantine/core', () => ({ Transition: ({ children }: any) => children, () => ({
  default: vi.fn(({ children, in: inProp, direction, ...props }) => {
    return inProp ? React.createElement('div', { ...props }, children) : null;
  })
}));

vi.mock('@mantine/core', () => ({ Transition: ({ children }: any) => children, () => ({
  default: vi.fn(({ children, in: inProp, ...props }) => {
    return inProp ? React.createElement('div', { ...props }, children) : null;
  })
}));

// Mock React Three Fiber for 3D components
vi.mock('@react-three/fiber', () => ({
  Canvas: vi.fn().mockImplementation(({ children, ...props }) => {
    return React.createElement('div', {
      'data-testid': 'three-canvas',
      ...props
    }, children);
  }),
  useFrame: vi.fn(),
  useThree: vi.fn(() => ({
    camera: {},
    scene: {},
    gl: {},
    size: { width: 800, height: 600 },
  })),
  useLoader: vi.fn(() => ({})),
  extend: vi.fn(),
  __esModule: true,
}));

vi.mock('@react-three/drei', () => ({
  OrbitControls: vi.fn().mockImplementation(() => null),
  Text: vi.fn().mockImplementation(({ children, ...props }) =>
    React.createElement('div', { 'data-testid': 'drei-text', ...props }, children)
  ),
  Box: vi.fn().mockImplementation((props) =>
    React.createElement('div', { 'data-testid': 'drei-box', ...props })
  ),
  Sphere: vi.fn().mockImplementation((props) =>
    React.createElement('div', { 'data-testid': 'drei-sphere', ...props })
  ),
  useGLTF: vi.fn(() => ({})),
  useTexture: vi.fn(() => ({})),
  Environment: vi.fn().mockImplementation(() => null),
  __esModule: true,
}));

// Mock Three.js core library
vi.mock('three', () => ({
  Scene: vi.fn(),
  PerspectiveCamera: vi.fn(),
  WebGLRenderer: vi.fn(),
  Mesh: vi.fn(),
  BoxGeometry: vi.fn(),
  SphereGeometry: vi.fn(),
  MeshBasicMaterial: vi.fn(),
  Vector3: vi.fn(),
  Color: vi.fn(),
  TextureLoader: vi.fn(),
  __esModule: true,
}));

// ============================================================================
// STANDARDIZED VI.MOCK() PATTERNS FOR MODULE RESOLUTION
// ============================================================================

// Mock the API service to prevent real network calls
vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    patch: vi.fn(() => Promise.resolve({ data: {} })),
  },
  apiClient: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    patch: vi.fn(() => Promise.resolve({ data: {} })),
  },
}));

// Mock dialog and widget components with consistent patterns
vi.mock('@/components/dialogs/CreateClassDialog', () => ({
  default: vi.fn().mockImplementation(({ open, onClose, onSave }) => {
    return open ? React.createElement('div', {
      'data-testid': 'create-class-dialog',
      onClick: () => onSave && onSave({ name: 'Test Class', grade: 10 })
    }, 'Create Class Dialog') : null;
  }),
  __esModule: true,
}));

vi.mock('@/components/widgets/StudentProgressTracker', () => ({
  default: vi.fn().mockImplementation(() => React.createElement('div', {
    'data-testid': 'student-progress-tracker'
  }, 'Student Progress Tracker')),
  __esModule: true,
}));

// Mock hooks with consistent patterns and proper ES module exports
vi.mock('@/hooks/useRealTimeData', () => ({
  default: vi.fn().mockReturnValue({
    data: null,
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
  __esModule: true,
}));

vi.mock('@/hooks/useApiData', () => ({
  useApiData: vi.fn().mockReturnValue({
    data: null,
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
  __esModule: true,
}));

// Mock config/routes with proper ES module exports
vi.mock('@/config/routes', () => ({
  ROUTES: {
    HOME: '/',
    CLASSES: '/classes',
    LESSONS: '/lessons',
    ASSESSMENTS: '/assessments',
    REPORTS: '/reports',
    SETTINGS: '/settings',
  },
  getClassDetailsRoute: vi.fn().mockImplementation((id) => `/classes/${id}`),
  __esModule: true,
}));

// Mock config/index with proper ES module exports
vi.mock('@/config/index', () => ({
  API_BASE_URL: 'http://localhost:8008',
  WS_URL: 'http://localhost:8008',
  PUSHER_KEY: 'test-pusher-key',
  PUSHER_CLUSTER: 'us2',
  PUSHER_AUTH_ENDPOINT: '/api/v1/pusher/auth',
  AUTH_TOKEN_KEY: 'toolboxai_auth_token',
  AUTH_REFRESH_TOKEN_KEY: 'toolboxai_refresh_token',
  ROBLOX_API_URL: 'https://api.roblox.com',
  ROBLOX_UNIVERSE_ID: 'test-universe-id',
  GOOGLE_CLASSROOM_CLIENT_ID: 'test-google-client-id',
  CANVAS_API_TOKEN: 'test-canvas-token',
  ENABLE_WEBSOCKET: true,
  ENABLE_GAMIFICATION: true,
  ENABLE_ANALYTICS: true,
  COPPA_COMPLIANCE: true,
  FERPA_COMPLIANCE: true,
  GDPR_COMPLIANCE: true,
  DEBUG_MODE: false,
  MOCK_API: false,
  XP_CONFIG: {
    levelMultiplier: 100,
    maxLevel: 100,
    bonusXPMultiplier: 1.5,
    streakBonus: 10,
  },
  PAGINATION: {
    defaultPageSize: 20,
    maxPageSize: 100,
  },
  WS_CONFIG: {
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
  },
  API_TIMEOUT: 30000,
  LANGUAGES: [
    { code: "en", name: "English" },
    { code: "es", name: "Español" },
    { code: "fr", name: "Français" },
  ],
  DEFAULT_LANGUAGE: "en",
  __esModule: true,
}));

// Mock relative config import path too
vi.mock('../../config', () => ({
  API_BASE_URL: 'http://localhost:8008',
  WS_URL: 'http://localhost:8008',
  PUSHER_KEY: 'test-pusher-key',
  PUSHER_CLUSTER: 'us2',
  PUSHER_AUTH_ENDPOINT: '/api/v1/pusher/auth',
  AUTH_TOKEN_KEY: 'toolboxai_auth_token',
  AUTH_REFRESH_TOKEN_KEY: 'toolboxai_refresh_token',
  ROBLOX_API_URL: 'https://api.roblox.com',
  ROBLOX_UNIVERSE_ID: 'test-universe-id',
  ENABLE_WEBSOCKET: true,
  ENABLE_GAMIFICATION: true,
  ENABLE_ANALYTICS: true,
  API_TIMEOUT: 30000,
  __esModule: true,
}));

// Mock WebSocketContext with consistent patterns
vi.mock('@/contexts/WebSocketContext', () => ({
  WebSocketProvider: vi.fn().mockImplementation(({ children }) => children),
  useWebSocket: vi.fn().mockReturnValue({
    isConnected: true,
    connectionState: 'connected',
    subscribe: vi.fn(() => ({ unsubscribe: vi.fn() })),
    unsubscribe: vi.fn(),
    emit: vi.fn(),
    on: vi.fn(() => ({ off: vi.fn() })),
    off: vi.fn(),
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    sendMessage: vi.fn(),
    lastMessage: null,
    error: null,
  }),
  WebSocketContext: {
    Provider: vi.fn().mockImplementation(({ children }) => children),
    Consumer: vi.fn(),
  },
  __esModule: true,
}));

// Mock the pusher service module - Updated for Pusher (not WebSocket)
vi.mock('@/services/pusher', () => {
  const mockChannels = new Map();

  const mockInstance = {
    // Connection management
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    reconnect: vi.fn().mockResolvedValue(undefined),
    isConnected: vi.fn(() => true),
    getConnectionState: vi.fn(() => 'connected'),

    // Channel subscription
    subscribe: vi.fn((channel) => {
      const mockChannel = {
        bind: vi.fn(),
        unbind: vi.fn(),
        trigger: vi.fn(),
        unsubscribe: vi.fn(),
      };
      mockChannels.set(channel, mockChannel);
      return mockChannel;
    }),
    unsubscribe: vi.fn((channel) => {
      mockChannels.delete(channel);
    }),

    // Event triggering
    trigger: vi.fn((channel, event, data) => ({
      status: 'success',
      messageId: `msg_${Date.now()}`
    })),

    // Authentication
    authenticate: vi.fn((channel, socketId) => ({
      auth: `${socketId}:${channel}:mock_auth`
    })),

    // Channel info
    getChannel: vi.fn((channel) => mockChannels.get(channel)),
    getChannels: vi.fn(() => Array.from(mockChannels.keys())),

    // Event handling
    on: vi.fn(),
    off: vi.fn(),

    // Auth token management
    setAuthToken: vi.fn(),
    clearAuthToken: vi.fn(),

    // Pusher specific
    getSocketId: vi.fn(() => `mock_socket_${Date.now()}`),
  };

  // Mock class constructor function
  const MockPusherService = vi.fn().mockImplementation(() => mockInstance);
  MockPusherService.getInstance = vi.fn().mockReturnValue(mockInstance);

  return {
    // Use function constructor pattern instead of object with getInstance
    PusherService: MockPusherService,

    // Also provide getInstance for backward compatibility
    getInstance: vi.fn().mockReturnValue(mockInstance),

    // Reset function for tests
    resetInstance: vi.fn().mockImplementation(() => {
      mockChannels.clear();
    }),

    // Default export
    default: mockInstance,

    // Export channel types
    ChannelType: {
      PUBLIC: 'public',
      PRIVATE: 'private',
      PRESENCE: 'presence'
    },

    // Export event names
    PusherEvents: {
      CONNECTED: 'pusher:connected',
      DISCONNECTED: 'pusher:disconnected',
      ERROR: 'pusher:error',
      SUBSCRIPTION_SUCCEEDED: 'pusher:subscription_succeeded',
      SUBSCRIPTION_ERROR: 'pusher:subscription_error',
      MEMBER_ADDED: 'pusher:member_added',
      MEMBER_REMOVED: 'pusher:member_removed'
    },

    __esModule: true,
  };
});

// Mock pusher service with relative import pattern too
vi.mock('../services/pusher', () => {
  const mockChannels = new Map();
  const mockInstance = {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    reconnect: vi.fn().mockResolvedValue(undefined),
    isConnected: vi.fn(() => true),
    getConnectionState: vi.fn(() => 'connected'),
    subscribe: vi.fn((channel) => {
      const mockChannel = {
        bind: vi.fn(),
        unbind: vi.fn(),
        trigger: vi.fn(),
        unsubscribe: vi.fn(),
      };
      mockChannels.set(channel, mockChannel);
      return mockChannel;
    }),
    unsubscribe: vi.fn((channel) => {
      mockChannels.delete(channel);
    }),
    trigger: vi.fn((channel, event, data) => ({
      status: 'success',
      messageId: `msg_${Date.now()}`
    })),
    authenticate: vi.fn((channel, socketId) => ({
      auth: `${socketId}:${channel}:mock_auth`
    })),
    getChannel: vi.fn((channel) => mockChannels.get(channel)),
    getChannels: vi.fn(() => Array.from(mockChannels.keys())),
    on: vi.fn(),
    off: vi.fn(),
    setAuthToken: vi.fn(),
    clearAuthToken: vi.fn(),
    getSocketId: vi.fn(() => `mock_socket_${Date.now()}`),
  };

  const MockPusherService = vi.fn().mockImplementation(() => mockInstance);
  MockPusherService.getInstance = vi.fn().mockReturnValue(mockInstance);

  return {
    PusherService: MockPusherService,
    getInstance: vi.fn().mockReturnValue(mockInstance),
    resetInstance: vi.fn().mockImplementation(() => {
      mockChannels.clear();
    }),
    default: mockInstance,
    __esModule: true,
  };
});

// Mock the websocket compatibility service
vi.mock('@/services/websocket', () => {
  const mockInstance = {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    isConnected: vi.fn(() => true),
    onStateChange: vi.fn(),
    onMessage: vi.fn(),
    onError: vi.fn(),
    send: vi.fn(),
    getState: vi.fn(() => 'connected'),
  };

  return {
    default: {
      getInstance: vi.fn().mockReturnValue(mockInstance),
    },
    WebSocketService: {
      getInstance: vi.fn().mockReturnValue(mockInstance),
    },
    connectWebSocket: vi.fn().mockResolvedValue(undefined),
    sendWebSocketMessage: vi.fn(),
    subscribeToWebSocket: vi.fn().mockReturnValue({ unsubscribe: vi.fn() }),
    unsubscribeFromWebSocket: vi.fn(),
    subscribeToChannel: vi.fn().mockReturnValue({ unsubscribe: vi.fn() }),
    unsubscribeFromChannel: vi.fn(),
    publishToChannel: vi.fn(),
    broadcastMessage: vi.fn(),
    __esModule: true,
  };
});

// Mock the WebSocket middleware to prevent real connections
vi.mock('@/store/middleware/websocketMiddleware', () => ({
  createWebSocketMiddleware: vi.fn().mockReturnValue(() => (next: any) => (action: any) => next(action)),
  setupWebSocketListeners: vi.fn(),
  __esModule: true,
}));

// ============================================================================
// VITEST 2.0 GLOBALS AND MATCHERS
// ============================================================================

// Extend Vitest's expect with jest-dom matchers for enhanced assertions
expect.extend(matchers);

// Set up global test environment variables
globalThis.__DEV__ = false;
globalThis.__TEST__ = true;

// ============================================================================
// POLYFILLS
// ============================================================================

// TextEncoder/TextDecoder polyfills for Node.js environment
// Fix for happy-dom environment compatibility
if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder;
}

// Additional polyfills for happy-dom environment
if (typeof global.structuredClone === 'undefined') {
  global.structuredClone = (obj: any) => JSON.parse(JSON.stringify(obj));
}

// React Three Fiber polyfills
if (typeof global.requestIdleCallback === 'undefined') {
  global.requestIdleCallback = (callback: any) => setTimeout(callback, 0);
}
if (typeof global.cancelIdleCallback === 'undefined') {
  global.cancelIdleCallback = (id: any) => clearTimeout(id);
}

// ============================================================================
// BROWSER API MOCKS
// ============================================================================

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn((key: string) => null),
  setItem: vi.fn((key: string, value: string) => undefined),
  removeItem: vi.fn((key: string) => undefined),
  clear: vi.fn(() => undefined),
  length: 0,
  key: vi.fn((index: number) => null)
};
global.localStorage = localStorageMock as Storage;

// Mock sessionStorage
global.sessionStorage = localStorageMock as Storage;

// Mock ResizeObserver for responsive components and charts
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

// Mock IntersectionObserver for lazy loading
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: []
}));

// Mock MutationObserver for DOM mutations
global.MutationObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  takeRecords: vi.fn(() => [])
}));

// Fix MutationObserver for testing-library
const mockMutationObserver = {
  observe: vi.fn(),
  disconnect: vi.fn(),
  takeRecords: vi.fn(() => [])
};
global.MutationObserver = vi.fn(() => mockMutationObserver);

// Mock matchMedia for responsive design
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
    dispatchEvent: vi.fn()
  }))
});

// ============================================================================
// CANVAS API MOCK (Comprehensive for Chart.js, Recharts, etc.)
// ============================================================================

const createCanvasRenderingContext2D = () => ({
  // Properties
  fillStyle: '',
  strokeStyle: '',
  shadowColor: '',
  shadowBlur: 0,
  shadowOffsetX: 0,
  shadowOffsetY: 0,
  lineWidth: 1,
  lineCap: 'butt',
  lineJoin: 'miter',
  miterLimit: 10,
  lineDashOffset: 0,
  font: '10px sans-serif',
  textAlign: 'start',
  textBaseline: 'alphabetic',
  globalAlpha: 1,
  globalCompositeOperation: 'source-over',
  
  // Path methods
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  fill: vi.fn(),
  
  // Rectangle methods
  rect: vi.fn(),
  fillRect: vi.fn(),
  strokeRect: vi.fn(),
  clearRect: vi.fn(),
  
  // Arc methods
  arc: vi.fn(),
  arcTo: vi.fn(),
  ellipse: vi.fn(),
  
  // Curve methods
  quadraticCurveTo: vi.fn(),
  bezierCurveTo: vi.fn(),
  
  // Text methods
  fillText: vi.fn(),
  strokeText: vi.fn(),
  measureText: vi.fn((text: string) => ({
    width: text.length * 10,
    actualBoundingBoxLeft: 0,
    actualBoundingBoxRight: text.length * 10,
    fontBoundingBoxAscent: 10,
    fontBoundingBoxDescent: 3,
    actualBoundingBoxAscent: 10,
    actualBoundingBoxDescent: 3
  })),
  
  // Image methods
  drawImage: vi.fn(),
  createImageData: vi.fn((width: number, height: number) => ({
    data: new Uint8ClampedArray(width * height * 4),
    width,
    height,
    colorSpace: 'srgb'
  })),
  getImageData: vi.fn((sx: number, sy: number, sw: number, sh: number) => ({
    data: new Uint8ClampedArray(sw * sh * 4),
    width: sw,
    height: sh,
    colorSpace: 'srgb'
  })),
  putImageData: vi.fn(),
  
  // Gradient and pattern
  createLinearGradient: vi.fn(() => ({
    addColorStop: vi.fn()
  })),
  createRadialGradient: vi.fn(() => ({
    addColorStop: vi.fn()
  })),
  createPattern: vi.fn(() => ({})),
  
  // Transformation methods
  save: vi.fn(),
  restore: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  translate: vi.fn(),
  transform: vi.fn(),
  setTransform: vi.fn(),
  resetTransform: vi.fn(),
  getTransform: vi.fn(() => ({
    a: 1, b: 0, c: 0, d: 1, e: 0, f: 0,
    m11: 1, m12: 0, m21: 0, m22: 1, m41: 0, m42: 0
  })),
  
  // Clipping
  clip: vi.fn(),
  
  // Line styles
  setLineDash: vi.fn(),
  getLineDash: vi.fn(() => []),
  
  // Focus management
  drawFocusIfNeeded: vi.fn(),
  
  // Canvas state
  isPointInPath: vi.fn(() => false),
  isPointInStroke: vi.fn(() => false),
  
  // Canvas element reference
  canvas: {
    width: 300,
    height: 150,
    getContext: vi.fn()
  }
});

// Mock Canvas getContext
HTMLCanvasElement.prototype.getContext = vi.fn().mockImplementation((contextType: string) => {
  if (contextType === '2d') {
    return createCanvasRenderingContext2D();
  }
  if (contextType === 'webgl' || contextType === 'webgl2') {
    // Basic WebGL context mock for 3D charts
    return {
      clearColor: vi.fn(),
      clear: vi.fn(),
      enable: vi.fn(),
      disable: vi.fn(),
      viewport: vi.fn(),
      getExtension: vi.fn(),
      getParameter: vi.fn(() => ''),
      createShader: vi.fn(() => ({})),
      shaderSource: vi.fn(),
      compileShader: vi.fn(),
      createProgram: vi.fn(() => ({})),
      attachShader: vi.fn(),
      linkProgram: vi.fn(),
      useProgram: vi.fn(),
      createBuffer: vi.fn(() => ({})),
      bindBuffer: vi.fn(),
      bufferData: vi.fn(),
      createTexture: vi.fn(() => ({})),
      bindTexture: vi.fn(),
      texImage2D: vi.fn(),
      texParameteri: vi.fn(),
      drawArrays: vi.fn(),
      drawElements: vi.fn()
    };
  }
  return null;
});

// Mock toDataURL and toBlob for canvas
HTMLCanvasElement.prototype.toDataURL = vi.fn(() => 'data:image/png;base64,');
HTMLCanvasElement.prototype.toBlob = vi.fn((callback: BlobCallback) => {
  callback(new Blob([''], { type: 'image/png' }));
});

// ============================================================================
// DOM API MOCKS
// ============================================================================

// Mock scrollIntoView for navigation tests
Element.prototype.scrollIntoView = vi.fn();

// Mock getBoundingClientRect for positioning calculations
Element.prototype.getBoundingClientRect = vi.fn(() => ({
  x: 0,
  y: 0,
  width: 100,
  height: 100,
  top: 0,
  right: 100,
  bottom: 100,
  left: 0,
  toJSON: () => ({})
}));

// Mock scroll methods
window.scrollTo = vi.fn() as any;
window.scroll = vi.fn() as any;

// ============================================================================
// WEB APIS MOCKS
// ============================================================================

// Mock Web Audio API for notification sounds
global.AudioContext = vi.fn().mockImplementation(() => ({
  createOscillator: vi.fn(() => ({
    connect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    type: 'sine',
    frequency: { value: 440 }
  })),
  createGain: vi.fn(() => ({
    connect: vi.fn(),
    gain: { value: 1 }
  })),
  createAnalyser: vi.fn(() => ({
    connect: vi.fn(),
    fftSize: 2048
  })),
  destination: {},
  currentTime: 0,
  close: vi.fn()
}));

// Mock Audio element
global.Audio = vi.fn().mockImplementation(() => ({
  play: vi.fn(() => Promise.resolve()),
  pause: vi.fn(),
  load: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  volume: 1,
  currentTime: 0,
  duration: 0,
  paused: true,
  ended: false
}));

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn((callback) => {
  setTimeout(callback, 0);
  return 0;
});

// Mock cancelAnimationFrame
global.cancelAnimationFrame = vi.fn();

// Mock performance API
global.performance.mark = vi.fn();
global.performance.measure = vi.fn();
global.performance.clearMarks = vi.fn();
global.performance.clearMeasures = vi.fn();

// Mock Notification API
global.Notification = vi.fn().mockImplementation(() => ({
  close: vi.fn(),
  addEventListener: vi.fn()
})) as any;
(global.Notification as any).permission = 'granted';
global.Notification.requestPermission = vi.fn(() => Promise.resolve('granted'));

// ============================================================================
// FETCH AND NETWORK MOCKS
// ============================================================================

// Mock fetch for API calls (if not already mocked by test)
if (!global.fetch) {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
      blob: () => Promise.resolve(new Blob()),
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
      headers: new Headers()
    } as Response)
  );
}

// ============================================================================
// CONSOLE CONFIGURATION
// ============================================================================

const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

// Filter out React warnings in tests
console.error = (...args: any[]) => {
  // Filter out known React warnings that don't affect tests
  const message = args[0]?.toString() || '';
  if (
    message.includes('Warning: ReactDOM.render') ||
    message.includes('Warning: unmountComponentAtNode') ||
    message.includes('Not implemented: navigation') ||
    message.includes('Not implemented: HTMLFormElement.submit')
  ) {
    return;
  }
  originalConsoleError.apply(console, args);
};

console.warn = (...args: any[]) => {
  const message = args[0]?.toString() || '';
  if (
    message.includes('Warning: ReactDOM.render') ||
    message.includes('experimental API')
  ) {
    return;
  }
  originalConsoleWarn.apply(console, args);
};

// ============================================================================
// TEST LIFECYCLE HOOKS
// ============================================================================

beforeAll(() => {
  // Set test environment for 2025 standards
  process.env.NODE_ENV = 'test';

  // Fix EventEmitter memory leak warnings by increasing max listeners
  process.setMaxListeners(50);

  // Mock environment variables with realistic test values
  process.env.VITE_API_BASE_URL = 'http://localhost:8008';
  process.env.VITE_WS_URL = 'ws://localhost:8008';
  process.env.VITE_PUSHER_KEY = 'test-pusher-key';
  process.env.VITE_PUSHER_CLUSTER = 'us2';
  process.env.VITE_ENABLE_WEBSOCKET = 'true';
  process.env.VITE_PUSHER_AUTH_ENDPOINT = '/pusher/auth';

  // Start MSW server with improved configuration
  server.listen({
    onUnhandledRequest: 'bypass', // Don't warn about unhandled requests in tests
  });

  // Configure test globals for Vitest 2.0
  vi.stubGlobal('__DEV__', false);
  vi.stubGlobal('__TEST__', true);

  // Note: Timer mocking is now handled per-test using timer-utils.ts
  // This prevents conflicts between tests that need different timer configurations
});

afterAll(() => {
  // Restore console methods
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;

  // Note: Timer cleanup is now handled per-test using timer-utils.ts

  // Stop MSW server
  server.close();
});

beforeEach(() => {
  // Clear all mocks
  vi.clearAllMocks();

  // Reset DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';

  // Reset MSW handlers to defaults
  server.resetHandlers();
});

afterEach(() => {
  // Cleanup React components
  cleanup();

  // Note: Timer cleanup is now handled per-test using timer-utils.ts

  // Clear localStorage/sessionStorage
  localStorage.clear();
  sessionStorage.clear();
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection in test:', promise, 'reason:', reason);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception in test:', error);
});

// ============================================================================
// GLOBAL TYPE DECLARATIONS
// ============================================================================

declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__?: any
  }
  
  var __DEV__: boolean;
  var __TEST__: boolean;
}

// Set global test flags
global.__DEV__ = false;
global.__TEST__ = true;

export {};