import React from 'react';
import ReactDOM from 'react-dom/client';
// Initialize console filter before any components load (suppress Mantine + React 19 warnings)
import { initConsoleFilter } from './utils/consoleFilter';
initConsoleFilter();

// HMR test comment - Hot module replacement working!
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { store } from './store';
import { theme } from './theme';
import './theme/global-styles.css';
import App from './App';
import './i18n/config';
import { ErrorBoundary } from './components/ErrorBoundary';
import { logger } from './utils/logger';

// Mantine Core Styles - Import all necessary CSS
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';

// Conditionally import Clerk components only when enabled
const isClerkEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';

// Import auth components - now they exist!
import ClerkProviderWrapper from './components/auth/ClerkProviderWrapper';
import { ClerkAuthProvider } from './contexts/ClerkAuthContext';
import { AuthProvider as LegacyAuthProvider } from './contexts/AuthContext';

// Clerk configuration validation
const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

// Enhanced error handling for Clerk configuration
if (!clerkPubKey && isClerkEnabled) {
  console.warn('Clerk authentication is enabled but no publishable key found. Set VITE_CLERK_PUBLISHABLE_KEY or disable with VITE_ENABLE_CLERK_AUTH=false');
}

// Create root app component with both auth providers
// Both providers are always present to support the useUnifiedAuth hook
const RootApp = () => {
  const appContent = (
    <Provider store={store}>
      <App />
    </Provider>
  );

  // Always wrap with both providers - they handle their own enabled/disabled state
  // This allows the useUnifiedAuth hook to work correctly without violating React rules
  if (isClerkEnabled) {
    return (
      <ClerkProviderWrapper>
        <ClerkAuthProvider>
          <LegacyAuthProvider>
            {appContent}
          </LegacyAuthProvider>
        </ClerkAuthProvider>
      </ClerkProviderWrapper>
    );
  }

  // When Clerk is disabled, still provide both providers for consistency
  return (
    <LegacyAuthProvider>
      {appContent}
    </LegacyAuthProvider>
  );
};

// Prevent multiple root creation in development (React 19 + HMR)
const rootElement = document.getElementById('root')!;

// Check if root already exists (for HMR)
if (!rootElement.hasAttribute('data-react-root')) {
  rootElement.setAttribute('data-react-root', 'true');

  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <MantineProvider theme={theme} defaultColorScheme="light">
        <Notifications position="top-right" limit={5} />
        <ErrorBoundary
          level="page"
          enableRecovery={true}
          enableReporting={true}
          onError={(error, errorInfo) => {
            logger.error('Application Error', { error, errorInfo });
            // In production, report to error tracking service
          }}
        >
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true
            }}
          >
            <RootApp />
          </BrowserRouter>
        </ErrorBoundary>
      </MantineProvider>
    </React.StrictMode>
  );
}