/**
 * Test Render Utilities
 * 
 * Custom render function that wraps components with all necessary providers
 * for testing in the ToolBoxAI Dashboard application.
 */

import React from 'react'
import { render as rtlRender, RenderOptions, RenderResult } from '@testing-library/react'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { configureStore, Store } from '@reduxjs/toolkit'
import { vi } from 'vitest'

// Import your actual store slices - adjust imports as needed
import uiReducer from '../../store/slices/uiSlice'
import userReducer from '../../store/slices/userSlice'
import dashboardReducer from '../../store/slices/dashboardSlice'
import gamificationReducer from '../../store/slices/gamificationSlice'
import messagesReducer from '../../store/slices/messagesSlice'
import progressReducer from '../../store/slices/progressSlice'
import assessmentsReducer from '../../store/slices/assessmentsSlice'
import complianceReducer from '../../store/slices/complianceSlice'

// Default theme for testing
const defaultTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
})

// Mock Pusher for all tests using the render utility
vi.mock('pusher-js', () => ({
  default: vi.fn(() => ({
    subscribe: vi.fn(() => ({
      bind: vi.fn(),
      unbind: vi.fn(),
      trigger: vi.fn(),
    })),
    unsubscribe: vi.fn(),
    disconnect: vi.fn(),
    connection: {
      bind: vi.fn(),
      unbind: vi.fn(),
      state: 'connected',
    },
  })),
}))

// Mock Socket.io for all tests
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    off: vi.fn(),
    emit: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    connected: true,
  })),
}))

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: any
  store?: Store
  theme?: any
  routerProps?: {
    initialEntries?: string[]
    initialIndex?: number
  }
}

/**
 * Creates a test store with optional preloaded state
 */
export function createTestStore(preloadedState?: any) {
  return configureStore({
    reducer: {
      ui: uiReducer,
      user: userReducer,
      dashboard: dashboardReducer,
      gamification: gamificationReducer,
      messages: messagesReducer,
      progress: progressReducer,
      assessments: assessmentsReducer,
      compliance: complianceReducer,
    },
    preloadedState,
  })
}

/**
 * All the providers for the app
 */
interface AllTheProvidersProps {
  children: React.ReactNode
  store?: Store
  theme?: any
  routerProps?: {
    initialEntries?: string[]
    initialIndex?: number
  }
}

function AllTheProviders({ 
  children, 
  store = createTestStore(), 
  theme = defaultTheme,
  routerProps = {}
}: AllTheProvidersProps) {
  return (
    <Provider store={store}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <ThemeProvider theme={theme}>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            {children}
          </LocalizationProvider>
        </ThemeProvider>
      </BrowserRouter>
    </Provider>
  )
}

/**
 * Custom render function that includes all providers
 * 
 * @example
 * ```tsx
 * import { render, screen } from '@test/utils/render'
 * 
 * test('renders component', () => {
 *   render(<MyComponent />, {
 *     preloadedState: {
 *       user: { isAuthenticated: true }
 *     }
 *   })
 *   expect(screen.getByText('Welcome')).toBeInTheDocument()
 * })
 * ```
 */
export function render(
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
): RenderResult {
  const {
    preloadedState,
    store = createTestStore(preloadedState),
    theme = defaultTheme,
    routerProps = {},
    ...renderOptions
  } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <AllTheProviders store={store} theme={theme} routerProps={routerProps}>
        {children}
      </AllTheProviders>
    )
  }

  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions })
}

/**
 * Custom render function for hooks
 */
export { renderHook } from '@testing-library/react'

// Re-export everything from React Testing Library
export * from '@testing-library/react'

// Export user event for convenience
export { default as userEvent } from '@testing-library/user-event'

// Export waitFor options
export const waitForOptions = {
  timeout: 5000,
  interval: 100,
}

/**
 * Helper to wait for async operations
 */
export async function waitForLoadingToFinish() {
  const { waitFor } = await import('@testing-library/react')
  await waitFor(
    () => {
      const loadingElements = document.querySelectorAll('[aria-busy="true"]')
      if (loadingElements.length > 0) {
        throw new Error('Still loading')
      }
    },
    waitForOptions
  )
}

/**
 * Mock API response helper
 */
export function mockApiResponse(data: any, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers({
      'content-type': 'application/json',
    }),
  } as Response)
}

/**
 * Create mock user for testing
 */
export function createMockUser(overrides = {}) {
  return {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    role: 'student',
    firstName: 'Test',
    lastName: 'User',
    isAuthenticated: true,
    ...overrides,
  }
}

/**
 * Create mock class for testing
 */
export function createMockClass(overrides = {}) {
  return {
    id: '1',
    name: 'Test Class',
    subject: 'Mathematics',
    grade: 5,
    teacherId: '1',
    studentCount: 25,
    ...overrides,
  }
}

/**
 * Helper to get elements by data-testid
 */
export function getByTestId(testId: string): HTMLElement | null {
  return document.querySelector(`[data-testid="${testId}"]`)
}

/**
 * Helper to get all elements by data-testid
 */
export function getAllByTestId(testId: string): HTMLElement[] {
  return Array.from(document.querySelectorAll(`[data-testid="${testId}"]`))
}