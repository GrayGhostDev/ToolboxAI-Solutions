/**
 * Test Render Utilities
 *
 * Custom render function that wraps components with all necessary providers
 * for testing in the ToolBoxAI Dashboard application.
 */
import React from 'react';
import { render as rtlRender, RenderOptions, RenderResult } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { configureStore, Store } from '@reduxjs/toolkit';
import { vi } from 'vitest';
// Import all store slices - using actual reducers from the slices
import uiReducer from '../../store/slices/uiSlice';
import userReducer from '../../store/slices/userSlice';
import dashboardReducer from '../../store/slices/dashboardSlice';
import gamificationReducer from '../../store/slices/gamificationSlice';
import messagesReducer from '../../store/slices/messagesSlice';
import progressReducer from '../../store/slices/progressSlice';
import assessmentsReducer from '../../store/slices/assessmentsSlice';
import complianceReducer from '../../store/slices/complianceSlice';
import analyticsReducer from '../../store/slices/analyticsSlice';
import classesReducer from '../../store/slices/classesSlice';
import lessonsReducer from '../../store/slices/lessonsSlice';
import realtimeReducer from '../../store/slices/realtimeSlice';
import robloxReducer from '../../store/slices/robloxSlice';
// Default theme factory for testing - optimized for 2025
function createDefaultTheme() {
  return createTheme({
    palette: {
      mode: 'light',
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
    },
    // Disable transitions for faster, more stable tests
    transitions: {
      create: () => 'none',
      duration: {
        shortest: 0,
        shorter: 0,
        short: 0,
        standard: 0,
        complex: 0,
        enteringScreen: 0,
        leavingScreen: 0,
      },
    },
    components: {
      // Disable animations and ripples for testing
      MuiButtonBase: {
        defaultProps: {
          disableRipple: true,
        },
      },
      MuiCssBaseline: {
        styleOverrides: {
          '*, *::before, *::after': {
            transition: 'none !important',
            animation: 'none !important',
          },
        },
      },
    },
  });
}
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
}));
// Note: Socket.IO mocks removed - now using Pusher for realtime
// Pusher is mocked in the main test setup file
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
  const reducer = {
    ui: uiReducer,
    user: userReducer,
    dashboard: dashboardReducer,
    gamification: gamificationReducer,
    messages: messagesReducer,
    progress: progressReducer,
    assessments: assessmentsReducer,
    compliance: complianceReducer,
    analytics: analyticsReducer,
    classes: classesReducer,
    lessons: lessonsReducer,
    realtime: realtimeReducer,
    roblox: robloxReducer,
  };
  return configureStore({
    reducer: reducer as any,
    preloadedState,
  });
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
  theme = createDefaultTheme(),
  routerProps = {}
}: AllTheProvidersProps) {
  const { initialEntries = ['/'], initialIndex = 0 } = routerProps;

  return (
    <Provider store={store}>
      <MemoryRouter
        initialEntries={initialEntries}
        initialIndex={initialIndex}
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
          v7_fetcherPersist: true,
          v7_normalizeFormMethod: true,
          v7_partialHydration: true,
          v7_skipActionErrorRevalidation: true,
        }}
      >
        <ThemeProvider theme={theme}>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            {children}
          </LocalizationProvider>
        </ThemeProvider>
      </MemoryRouter>
    </Provider>
  );
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
    theme = createDefaultTheme(),
    routerProps = {},
    ...renderOptions
  } = options;
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <AllTheProviders store={store} theme={theme} routerProps={routerProps}>
        {children}
      </AllTheProviders>
    );
  }
  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
}
/**
 * Re-export from React Testing Library
 */
export {
  renderHook,
  cleanup,
  act
} from '@testing-library/react';
// Re-export testing utilities
export * from '@testing-library/react';
// Export user event for convenience
export { default as userEvent } from '@testing-library/user-event';
// Export waitFor options
export const waitForOptions = {
  timeout: 5000,
  interval: 100,
};
/**
 * Helper to wait for async operations
 */
export async function waitForLoadingToFinish() {
  // Simple timeout-based waiting for loading to finish
  const maxWaitTime = 5000;
  const checkInterval = 100;
  let elapsed = 0;
  while (elapsed < maxWaitTime) {
    const loadingElements = document.querySelectorAll('[aria-busy="true"]');
    if (loadingElements.length === 0) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, checkInterval));
    elapsed += checkInterval;
  }
  throw new Error('Loading did not finish within timeout');
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
  } as Response);
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
  };
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
  };
}