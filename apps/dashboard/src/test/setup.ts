/**
 * Test Setup for ToolBoxAI Dashboard
 * 
 * This file configures the test environment with all necessary polyfills,
 * mocks, and utilities for comprehensive testing with Vitest.
 * 
 * @vitest-environment jsdom
 */

import '@testing-library/jest-dom'
import { beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'
import { expect } from 'vitest'
import { TextEncoder, TextDecoder } from 'util'
import { server } from './utils/msw-handlers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// ============================================================================
// POLYFILLS
// ============================================================================

// TextEncoder/TextDecoder polyfills for Node.js environment
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as any

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
}
global.localStorage = localStorageMock as Storage

// Mock sessionStorage
global.sessionStorage = localStorageMock as Storage

// Mock ResizeObserver for responsive components and charts
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock IntersectionObserver for lazy loading
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: []
}))

// Mock MutationObserver for DOM mutations
global.MutationObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  takeRecords: vi.fn(() => [])
}))

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
})

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
})

// Mock Canvas getContext
HTMLCanvasElement.prototype.getContext = vi.fn().mockImplementation((contextType: string) => {
  if (contextType === '2d') {
    return createCanvasRenderingContext2D()
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
    }
  }
  return null
})

// Mock toDataURL and toBlob for canvas
HTMLCanvasElement.prototype.toDataURL = vi.fn(() => 'data:image/png;base64,')
HTMLCanvasElement.prototype.toBlob = vi.fn((callback: BlobCallback) => {
  callback(new Blob([''], { type: 'image/png' }))
})

// ============================================================================
// DOM API MOCKS
// ============================================================================

// Mock scrollIntoView for navigation tests
Element.prototype.scrollIntoView = vi.fn()

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
}))

// Mock scroll methods
window.scrollTo = vi.fn()
window.scroll = vi.fn()

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
}))

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
}))

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn((callback) => {
  setTimeout(callback, 0)
  return 0
})

// Mock cancelAnimationFrame
global.cancelAnimationFrame = vi.fn()

// Mock performance API
global.performance.mark = vi.fn()
global.performance.measure = vi.fn()
global.performance.clearMarks = vi.fn()
global.performance.clearMeasures = vi.fn()

// Mock Notification API
global.Notification = vi.fn().mockImplementation(() => ({
  close: vi.fn(),
  addEventListener: vi.fn()
})) as any
global.Notification.permission = 'granted'
global.Notification.requestPermission = vi.fn(() => Promise.resolve('granted'))

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
  )
}

// ============================================================================
// CONSOLE CONFIGURATION
// ============================================================================

const originalConsoleError = console.error
const originalConsoleWarn = console.warn

// Filter out React warnings in tests
console.error = (...args: any[]) => {
  // Filter out known React warnings that don't affect tests
  const message = args[0]?.toString() || ''
  if (
    message.includes('Warning: ReactDOM.render') ||
    message.includes('Warning: unmountComponentAtNode') ||
    message.includes('Not implemented: navigation') ||
    message.includes('Not implemented: HTMLFormElement.submit')
  ) {
    return
  }
  originalConsoleError.apply(console, args)
}

console.warn = (...args: any[]) => {
  const message = args[0]?.toString() || ''
  if (
    message.includes('Warning: ReactDOM.render') ||
    message.includes('experimental API')
  ) {
    return
  }
  originalConsoleWarn.apply(console, args)
}

// ============================================================================
// TEST LIFECYCLE HOOKS
// ============================================================================

beforeAll(() => {
  // Set test environment
  process.env.NODE_ENV = 'test'

  // Mock environment variables
  process.env.VITE_API_BASE_URL = 'http://localhost:8008'
  process.env.VITE_WS_URL = 'ws://localhost:8008'
  process.env.VITE_PUSHER_KEY = 'test-pusher-key'
  process.env.VITE_PUSHER_CLUSTER = 'us2'

  // Start MSW server
  server.listen({
    onUnhandledRequest: 'bypass', // Don't warn about unhandled requests
  })
})

afterAll(() => {
  // Restore console methods
  console.error = originalConsoleError
  console.warn = originalConsoleWarn

  // Stop MSW server
  server.close()
})

beforeEach(() => {
  // Clear all mocks
  vi.clearAllMocks()

  // Reset DOM
  document.body.innerHTML = ''
  document.head.innerHTML = ''

  // Reset MSW handlers to defaults
  server.resetHandlers()
})

afterEach(() => {
  // Cleanup React components
  cleanup()

  // Clear all timers
  vi.clearAllTimers()

  // Clear localStorage/sessionStorage
  localStorage.clear()
  sessionStorage.clear()
})

// ============================================================================
// ERROR HANDLING
// ============================================================================

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection in test:', promise, 'reason:', reason)
})

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception in test:', error)
})

// ============================================================================
// GLOBAL TYPE DECLARATIONS
// ============================================================================

declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__?: any
  }
  
  var __DEV__: boolean
  var __TEST__: boolean
}

// Set global test flags
global.__DEV__ = false
global.__TEST__ = true

export {}