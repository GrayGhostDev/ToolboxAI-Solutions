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