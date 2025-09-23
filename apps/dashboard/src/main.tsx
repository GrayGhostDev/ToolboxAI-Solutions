import React from "react";
import ReactDOM from "react-dom/client";
// HMR test comment - Hot module replacement working!
import { Provider } from "react-redux";
import { BrowserRouter } from "react-router-dom";
import { store } from "./store";
import "./theme/injectAnimations";
import App from "./App";
import "./i18n/config";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ThemeWrapper } from "./components/ThemeWrapper";
import { logger } from "./utils/logger";

// Conditionally import Clerk components only when enabled
const isClerkEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';

// Lazy load auth components to avoid import errors
const ClerkProviderWrapper = isClerkEnabled
  ? React.lazy(() => import("./components/auth/ClerkProviderWrapper").then(m => ({ default: m.ClerkProviderWrapper })))
  : null;
const ClerkAuthProvider = isClerkEnabled
  ? React.lazy(() => import("./contexts/ClerkAuthContext").then(m => ({ default: m.ClerkAuthProvider })))
  : null;

// Load legacy auth provider when Clerk is disabled
const LegacyAuthProvider = !isClerkEnabled
  ? React.lazy(() => import("./contexts/AuthContext").then(m => ({ default: m.AuthProvider })))
  : null;

// Clerk configuration validation
const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

// Enhanced error handling for Clerk configuration
if (!clerkPubKey && isClerkEnabled) {
  console.warn("Clerk authentication is enabled but no publishable key found. Set VITE_CLERK_PUBLISHABLE_KEY or disable with VITE_ENABLE_CLERK_AUTH=false");
}

// Create root app component with conditional Clerk wrapping
const RootApp = () => {
  const appContent = (
    <Provider store={store}>
      <ThemeWrapper>
        <App />
      </ThemeWrapper>
    </Provider>
  );

  // Wrap with Clerk providers only if enabled
  if (isClerkEnabled && ClerkProviderWrapper && ClerkAuthProvider) {
    return (
      <React.Suspense fallback={<div>Loading authentication...</div>}>
        <ClerkProviderWrapper publishableKey={clerkPubKey}>
          <ClerkAuthProvider>
            {appContent}
          </ClerkAuthProvider>
        </ClerkProviderWrapper>
      </React.Suspense>
    );
  }

  // Wrap with legacy auth provider when Clerk is disabled
  if (!isClerkEnabled && LegacyAuthProvider) {
    return (
      <React.Suspense fallback={<div>Loading authentication...</div>}>
        <LegacyAuthProvider>
          {appContent}
        </LegacyAuthProvider>
      </React.Suspense>
    );
  }

  // Fallback - return app without any auth provider (should not happen)
  console.warn('No auth provider available - this may cause authentication errors');
  return appContent;
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary
      level="page"
      enableRecovery={true}
      enableReporting={true}
      onError={(error, errorInfo) => {
        logger.error('Application Error', { error, errorInfo });
        // In production, report to error tracking service
      }}
    >
      <BrowserRouter>
        <RootApp />
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
);