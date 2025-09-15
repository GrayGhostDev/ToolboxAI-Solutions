import * as React from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
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
import PasswordReset from "./components/pages/PasswordReset";
import { useAuth } from "./hooks/useAuth";
import ErrorBoundary from "./components/common/ErrorBoundary";
import { WebSocketProvider } from "./contexts/WebSocketContext";

// Terminal services removed - not part of application
// Performance monitor disabled due to performance issues
// import { performanceMonitor } from "./utils/performance-monitor";

export default function App() {
  const role = useAppSelector((s) => s.user.role);
  const isAuthenticated = useAppSelector((s) => s.user.isAuthenticated);
  const loading = useAppSelector((s) => s.ui.loading);
  const [consentGiven, setConsentGiven] = React.useState(false);
  const [showConsent, setShowConsent] = React.useState(false);
  const navigate = useNavigate();

  // Initialize authentication and persistence
  useAuth();

  // Performance monitoring disabled to improve app performance
  // The monitoring itself was causing severe slowdowns (20-30 second renders)
  React.useEffect(() => {
    // Temporarily disabled performance monitoring
    // Uncomment below to re-enable when performance issues are resolved
    /*
    if (isAuthenticated) {
      console.log('🚀 Initializing performance monitoring');
      
      // Start performance monitoring
      if (!performanceMonitor.isRunning()) {
        performanceMonitor.startMonitoring();
        console.log('✅ Performance monitoring started');
      }
    } else {
      // Clean up services when not authenticated
      if (performanceMonitor.isRunning()) {
        performanceMonitor.stopMonitoring();
        console.log('🛑 Performance monitoring stopped');
      }
    }
    */
    
    // Cleanup on unmount
    return () => {
      // Disabled for now
      /*
      if (performanceMonitor.isRunning()) {
        performanceMonitor.stopMonitoring();
      }
      */
    };
  }, [isAuthenticated]);

  React.useEffect(() => {
    // Check if COPPA consent is needed
    if (COPPA_COMPLIANCE && role === "student" && !consentGiven) {
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
      // Navigate to dashboard after consent is accepted
      navigate('/dashboard');
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
          <Route path="/password-reset" element={<PasswordReset />} />
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
      <WebSocketProvider autoConnect={true}>
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
      </WebSocketProvider>
    </ErrorBoundary>
  );
}