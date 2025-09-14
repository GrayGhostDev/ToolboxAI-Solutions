/**
 * Debug Test Setup for ToolBoxAI Dashboard
 *
 * This file configures the test environment with debugging capabilities
 * including enhanced logging, error handling, and debugging utilities.
 */

import '@testing-library/jest-dom'
import { beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'
import { expect } from 'vitest'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
}
global.localStorage = localStorageMock as Storage

// Mock sessionStorage
global.sessionStorage = localStorageMock as Storage

// Mock ResizeObserver for Material-UI components
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock IntersectionObserver for lazy loading components
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: []
}))

// Mock matchMedia for responsive components
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
})

// Mock Canvas API for chart components
HTMLCanvasElement.prototype.getContext = vi.fn().mockImplementation((contextType) => {
  if (contextType === '2d') {
    return {
      fillStyle: '',
      strokeStyle: '',
      lineWidth: 1,
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      closePath: vi.fn(),
      fill: vi.fn(),
      stroke: vi.fn(),
      rect: vi.fn(),
      fillRect: vi.fn(),
      strokeRect: vi.fn(),
      clearRect: vi.fn(),
      arc: vi.fn(),
      arcTo: vi.fn(),
      createLinearGradient: vi.fn(() => ({
        addColorStop: vi.fn()
      })),
      createRadialGradient: vi.fn(() => ({
        addColorStop: vi.fn()
      })),
      measureText: vi.fn(() => ({ width: 0 })),
      fillText: vi.fn(),
      strokeText: vi.fn(),
      save: vi.fn(),
      restore: vi.fn(),
      scale: vi.fn(),
      rotate: vi.fn(),
      translate: vi.fn(),
      transform: vi.fn(),
      setTransform: vi.fn()
    }
  }
  return null
})

// Mock scrollIntoView for navigation tests
Element.prototype.scrollIntoView = vi.fn()

// Mock Web Audio API for notification sounds
global.AudioContext = vi.fn().mockImplementation(() => ({
  createOscillator: vi.fn(),
  createGain: vi.fn(),
  destination: {}
}))

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn().mockImplementation(cb => {
  setTimeout(cb, 0)
  return 0
})

// Mock cancelAnimationFrame
global.cancelAnimationFrame = vi.fn()

// Debug logging configuration
const originalConsoleError = console.error
const originalConsoleWarn = console.warn

// Enhanced error logging for debugging
console.error = (...args: any[]) => {
  if (args[0]?.includes?.('Warning:') || args[0]?.includes?.('Error:')) {
    originalConsoleError(...args)
  }
}

console.warn = (...args: any[]) => {
  if (args[0]?.includes?.('Warning:')) {
    originalConsoleWarn(...args)
  }
}

// Debug test environment setup
beforeAll(() => {
  // Enable debug mode
  process.env.NODE_ENV = 'test'
  process.env.DEBUG = 'true'

  // Mock environment variables for testing
  process.env.VITE_API_BASE_URL = 'http://localhost:8008'
  process.env.VITE_WS_URL = 'ws://localhost:8008'

  // Setup global test utilities
  global.testUtils = {
    debug: true,
    logLevel: 'debug',
    mockData: {},
    testHelpers: {}
  }
})

// Debug test cleanup
afterAll(() => {
  // Restore original console methods
  console.error = originalConsoleError
  console.warn = originalConsoleWarn

  // Cleanup global test utilities
  delete global.testUtils
})

// Debug test setup for each test
beforeEach(() => {
  // Clear all mocks
  vi.clearAllMocks()

  // Reset DOM
  document.body.innerHTML = ''

  // Setup debug logging for current test
  if (global.testUtils?.debug) {
    console.log(`[DEBUG] Starting test: ${expect.getState().currentTestName}`)
  }
})

// Debug test cleanup for each test
afterEach(() => {
  // Cleanup DOM
  cleanup()

  // Debug test completion
  if (global.testUtils?.debug) {
    console.log(`[DEBUG] Completed test: ${expect.getState().currentTestName}`)
  }
})

// Debug error handling
process.on('unhandledRejection', (reason, promise) => {
  console.error('[DEBUG] Unhandled Rejection at:', promise, 'reason:', reason)
})

process.on('uncaughtException', (error) => {
  console.error('[DEBUG] Uncaught Exception:', error)
})

// Debug test utilities
export const debugTestUtils = {
  // Log test information
  logTestInfo: (testName: string, info: any) => {
    if (global.testUtils?.debug) {
      console.log(`[DEBUG] ${testName}:`, info)
    }
  },

  // Mock API responses
  mockApiResponse: (url: string, response: any) => {
    if (global.testUtils?.mockData) {
      global.testUtils.mockData[url] = response
    }
  },

  // Get mock data
  getMockData: (url: string) => {
    return global.testUtils?.mockData?.[url] || null
  },

  // Clear mock data
  clearMockData: () => {
    if (global.testUtils?.mockData) {
      global.testUtils.mockData = {}
    }
  },

  // Debug component rendering
  debugRender: (component: any, props: any = {}) => {
    if (global.testUtils?.debug) {
      console.log('[DEBUG] Rendering component:', component.name || 'Unknown', 'with props:', props)
    }
  },

  // Debug API calls
  debugApiCall: (method: string, url: string, data?: any) => {
    if (global.testUtils?.debug) {
      console.log(`[DEBUG] API ${method.toUpperCase()}:`, url, data ? 'with data:' : '', data || '')
    }
  },

  // Debug state changes
  debugStateChange: (stateName: string, oldState: any, newState: any) => {
    if (global.testUtils?.debug) {
      console.log(`[DEBUG] State change in ${stateName}:`, {
        from: oldState,
        to: newState
      })
    }
  }
}

// Global type declarations for test utilities
declare global {
  var testUtils: {
    debug: boolean
    logLevel: string
    mockData: Record<string, any>
    testHelpers: Record<string, any>
  } | undefined
}

// Export debug utilities
export default debugTestUtils