/**
 * Custom Render Utility - 2025 Standards
 *
 * Provides a custom render function that wraps components with all necessary
 * providers: Redux, React Router, Mantine theme, and Pusher context.
 *
 * Compatible with React 19.1.0, Mantine 8.x, and Vitest 3.2.4
 */

import React from 'react';
import { render as rtlRender, type RenderOptions, type RenderResult } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { configureStore, type PreloadedState } from '@reduxjs/toolkit';

// Import all Redux slices
import userSlice from '@/store/slices/userSlice';
import uiSlice from '@/store/slices/uiSlice';
import dashboardSlice from '@/store/slices/dashboardSlice';
import assessmentsSlice from '@/store/slices/assessmentsSlice';
import complianceSlice from '@/store/slices/complianceSlice';
import messagesSlice from '@/store/slices/messagesSlice';
import progressSlice from '@/store/slices/progressSlice';
import gamificationSlice from '@/store/slices/gamificationSlice';
import analyticsSlice from '@/store/slices/analyticsSlice';
import classesSlice from '@/store/slices/classesSlice';
import lessonsSlice from '@/store/slices/lessonsSlice';
import realtimeSlice from '@/store/slices/realtimeSlice';
import robloxSlice from '@/store/slices/robloxSlice';

// Import Mantine theme
import { mantineTheme as theme } from '@/theme/mantine-theme';

// Root reducer for type inference
const rootReducer = {
  user: userSlice,
  ui: uiSlice,
  dashboard: dashboardSlice,
  assessments: assessmentsSlice,
  compliance: complianceSlice,
  messages: messagesSlice,
  progress: progressSlice,
  gamification: gamificationSlice,
  analytics: analyticsSlice,
  classes: classesSlice,
  lessons: lessonsSlice,
  realtime: realtimeSlice,
  roblox: robloxSlice,
};

// Infer types first
export type RootState = ReturnType<ReturnType<typeof configureStore<typeof rootReducer>>['getState']>;

/**
 * Create a test Redux store with all slices
 */
export function createTestStore(preloadedState?: PreloadedState<RootState>) {
  return configureStore({
    reducer: rootReducer,
    preloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false, // Disable for testing
        immutableCheck: false,    // Disable for testing performance
      }),
  });
}

// Export store type for TypeScript
export type AppStore = ReturnType<typeof createTestStore>;
export type AppDispatch = AppStore['dispatch'];

/**
 * Custom render options extending React Testing Library
 */
export interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  /** Preloaded Redux state */
  preloadedState?: PreloadedState<RootState>;
  /** Custom Redux store (optional) */
  store?: AppStore;
  /** React Router props */
  routerProps?: MemoryRouterProps;
}

/**
 * Custom render result with store access
 */
export interface CustomRenderResult extends RenderResult {
  store: AppStore;
}

/**
 * All-in-one test wrapper with all providers
 */
function AllTheProviders({
  children,
  store,
  routerProps = {},
}: {
  children: React.ReactNode;
  store: AppStore;
  routerProps?: MemoryRouterProps;
}) {
  return (
    <Provider store={store}>
      <MemoryRouter {...routerProps}>
        <MantineProvider theme={theme}>
          <Notifications />
          {children}
        </MantineProvider>
      </MemoryRouter>
    </Provider>
  );
}

/**
 * Custom render function with all providers
 *
 * @example
 * ```tsx
 * import { render, screen } from '@test/utils/render';
 *
 * it('renders component', () => {
 *   render(<MyComponent />);
 *   expect(screen.getByText('Hello')).toBeInTheDocument();
 * });
 *
 * // With custom state
 * it('renders with state', () => {
 *   render(<MyComponent />, {
 *     preloadedState: {
 *       user: { currentUser: { name: 'Test' } }
 *     }
 *   });
 * });
 *
 * // With router
 * it('renders with routing', () => {
 *   render(<MyComponent />, {
 *     routerProps: {
 *       initialEntries: ['/dashboard'],
 *       initialIndex: 0
 *     }
 *   });
 * });
 * ```
 */
export function render(
  ui: React.ReactElement,
  {
    preloadedState,
    store = createTestStore(preloadedState),
    routerProps,
    ...renderOptions
  }: CustomRenderOptions = {}
): CustomRenderResult {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <AllTheProviders store={store} routerProps={routerProps}>
      {children}
    </AllTheProviders>
  );

  const renderResult = rtlRender(ui, { wrapper: Wrapper, ...renderOptions });

  return {
    ...renderResult,
    store,
  };
}

/**
 * Re-export everything from React Testing Library
 * This allows users to import everything from a single location
 */
export * from '@testing-library/react';

// Don't re-export the default render, use our custom one
export { render as default };
