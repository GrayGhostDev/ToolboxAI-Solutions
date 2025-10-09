import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import React, { type ReactElement } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { type Store } from '@reduxjs/toolkit';
import { store as defaultStore } from '../store';
import { theme } from '../theme/mantine-theme';

interface AllTheProvidersProps {
  children: React.ReactNode;
  store?: Store;
}

/**
 * Custom render function that includes all necessary providers
 * with React Router v7 future flags enabled
 */
function AllTheProviders({ children, store = defaultStore }: AllTheProvidersProps) {
  return (
    <Provider store={store}>
      <MantineProvider theme={theme}>
        <Notifications />
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true
          }}
        >
          {children}
        </BrowserRouter>
      </MantineProvider>
    </Provider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  store?: Store;
}

/**
 * Custom render method that wraps components with all required providers
 * Use this instead of the default render from @testing-library/react
 * 
 * @example
 * ```tsx
 * import { renderWithProviders } from '../test/test-utils';
 * 
 * test('my component test', () => {
 *   const { getByText } = renderWithProviders(<MyComponent />);
 *   expect(getByText('Hello')).toBeInTheDocument();
 * });
 * ```
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: CustomRenderOptions
): ReturnType<typeof render> {
  const { store, ...renderOptions } = options || {};
  
  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders store={store}>{children}</AllTheProviders>
    ),
    ...renderOptions
  });
}

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { renderWithProviders as render };