import React from "react";
import ReactDOM from "react-dom/client";
import { Provider } from "react-redux";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { store } from "./store";
import { robloxTheme } from "./theme";
import App from "./App";
import "./i18n/config";
import { ErrorBoundary } from "./components/ErrorBoundary";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary
      level="page"
      enableRecovery={true}
      enableReporting={true}
      onError={(error, errorInfo) => {
        console.error('Application Error:', error, errorInfo);
        // In production, report to error tracking service
      }}
    >
      <Provider store={store}>
        <ThemeProvider theme={robloxTheme}>
          <CssBaseline />
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true
            }}
          >
            <App />
          </BrowserRouter>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  </React.StrictMode>
);