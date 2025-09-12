import * as React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import { useAppSelector } from "./store";
import AppRoutes from "./routes";
import { ConsentModal } from "./components/modals/ConsentModal";
import { NotificationToast } from "./components/notifications/NotificationToast";
import RealtimeToast from "./components/notifications/RealtimeToast";
import { LoadingOverlay } from "./components/common/LoadingOverlay";
import { COPPA_COMPLIANCE } from "./config";
import Login from "./components/pages/Login";
import Register from "./components/pages/Register";
import { useAuth } from "./hooks/useAuth";
import ErrorBoundary from "./components/common/ErrorBoundary";

export default function App() {
  const role = useAppSelector((s) => s.user.role);
  const isAuthenticated = useAppSelector((s) => s.user.isAuthenticated);
  const loading = useAppSelector((s) => s.ui.loading);
  const [consentGiven, setConsentGiven] = React.useState(false);
  const [showConsent, setShowConsent] = React.useState(false);

  // Initialize authentication and persistence
  useAuth();

  React.useEffect(() => {
    // Check if COPPA consent is needed
    if (COPPA_COMPLIANCE && role === "Student" && !consentGiven) {
      const consent = localStorage.getItem("coppa_consent");
      if (!consent) {
        setShowConsent(true);
      } else {
        setConsentGiven(true);
      }
    }
  }, [role, consentGiven]);

  const handleConsentClose = (accepted: boolean) => {
    if (accepted) {
      localStorage.setItem("coppa_consent", "true");
      setConsentGiven(true);
    }
    setShowConsent(false);
  };

  // If not authenticated, show auth routes
  if (!isAuthenticated) {
    return (
      <ErrorBoundary>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        
        {/* Global Components */}
        <NotificationToast />
        {loading && <LoadingOverlay />}
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <AppLayout role={role}>
        <AppRoutes />
      </AppLayout>
      
      {/* Global Components */}
      <NotificationToast />
      <RealtimeToast />
      {loading && <LoadingOverlay />}
      
      {/* COPPA Consent Modal */}
      {showConsent && (
        <ConsentModal 
          open={showConsent} 
          onClose={handleConsentClose}
        />
      )}
    </ErrorBoundary>
  );
}