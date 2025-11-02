import React from 'react';
import ReactDOM from 'react-dom/client';
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
import { unregisterServiceWorkers } from './utils/serviceWorkerCleanup';

// Initialize Sentry monitoring
import { initSentry } from './config/sentry';

// Suppress non-critical HMR WebSocket errors in Docker/development
import './utils/hmrErrorSuppressor';

// Mantine Core Styles - Import all necessary CSS
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';

// Initialize Sentry for error tracking in production
initSentry();

// Clean up any old service workers on app start
// This prevents errors from previously registered service workers
if (process.env.NODE_ENV === 'development') {
  unregisterServiceWorkers().catch(error => {
    console.warn('Failed to unregister service workers:', error);
  });
}

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
// Redux Provider must be at the top since auth providers use Redux hooks
const RootApp = () => {
  // Always wrap with both providers - they handle their own enabled/disabled state
  // This allows the useUnifiedAuth hook to work correctly without violating React rules
  if (isClerkEnabled) {
    return (
      <Provider store={store}>
        <ClerkProviderWrapper>
          <ClerkAuthProvider>
            <LegacyAuthProvider>
              <App />
            </LegacyAuthProvider>
          </ClerkAuthProvider>
        </ClerkProviderWrapper>
      </Provider>
    );
  }

  // When Clerk is disabled, still provide both providers for consistency
  return (
    <Provider store={store}>
      <LegacyAuthProvider>
        <App />
      </LegacyAuthProvider>
    </Provider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
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