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

// Import auth components - now they exist!
import ClerkProviderWrapper from "./components/auth/ClerkProviderWrapper";
import { ClerkAuthProvider } from "./contexts/ClerkAuthContext";
import { AuthProvider as LegacyAuthProvider } from "./contexts/AuthContext";

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
  if (isClerkEnabled) {
    return (
      <ClerkProviderWrapper>
        <ClerkAuthProvider>
          {appContent}
        </ClerkAuthProvider>
      </ClerkProviderWrapper>
    );
  }

  // Wrap with legacy auth provider when Clerk is disabled
  return (
    <LegacyAuthProvider>
      {appContent}
    </LegacyAuthProvider>
  );
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