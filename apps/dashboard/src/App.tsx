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
import PasswordReset from "./components/pages/PasswordReset";
import { useAuth } from "./hooks/useAuth";
import ErrorBoundary from "./components/common/ErrorBoundary";
import { WebSocketProvider } from "./contexts/WebSocketContext";

// Terminal verification and monitoring services
import { terminalVerifier } from "./utils/terminal-verify";
import { terminalSync } from "./services/terminal-sync";
import { performanceMonitor } from "./utils/performance-monitor";

export default function App() {
  const role = useAppSelector((s) => s.user.role);
  const isAuthenticated = useAppSelector((s) => s.user.isAuthenticated);
  const loading = useAppSelector((s) => s.ui.loading);
  const [consentGiven, setConsentGiven] = React.useState(false);
  const [showConsent, setShowConsent] = React.useState(false);

  // Initialize authentication and persistence
  useAuth();

  // Initialize terminal services when authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      console.log('🚀 Initializing Terminal 2 services');
      
      // Initialize terminal sync service
      terminalSync.initialize().then(() => {
        console.log('✅ Terminal sync service initialized');
        
        // Start terminal verification monitoring
        if (!terminalVerifier.isMonitoring()) {
          terminalVerifier.startMonitoring();
          console.log('✅ Terminal verification monitoring started');
        }
        
        // Start performance monitoring
        if (!performanceMonitor.isRunning()) {
          performanceMonitor.startMonitoring();
          console.log('✅ Performance monitoring started');
        }
        
        // Set up cross-terminal communication handlers
        terminalSync.on('message:verification_request', (payload: any) => {
          console.log('📨 Received verification request from', payload.from);
          terminalVerifier.runVerification().catch(error => {
            console.error('❌ Verification request failed:', error);
          });
        });
        
        terminalSync.on('performance_alert', (alert: any) => {
          console.warn('⚠️ Performance alert received:', alert);
          // Could trigger UI notifications here
        });
        
        terminalSync.on('system_alert', (alert: any) => {
          console.warn('🚨 System alert received:', alert);
          // Could trigger UI notifications here
        });
        
      }).catch(error => {
        console.error('❌ Failed to initialize terminal sync:', error);
        // Fallback: still try to start individual services
        if (!terminalVerifier.isMonitoring()) {
          terminalVerifier.startMonitoring();
        }
        if (!performanceMonitor.isRunning()) {
          performanceMonitor.startMonitoring();
        }
      });
    } else {
      // Clean up services when not authenticated
      if (terminalVerifier.isMonitoring()) {
        terminalVerifier.stopMonitoring();
        console.log('🛑 Terminal verification monitoring stopped');
      }
      if (performanceMonitor.isRunning()) {
        performanceMonitor.stopMonitoring();
        console.log('🛑 Performance monitoring stopped');
      }
    }
    
    // Cleanup on unmount
    return () => {
      if (terminalVerifier.isMonitoring()) {
        terminalVerifier.stopMonitoring();
      }
      if (performanceMonitor.isRunning()) {
        performanceMonitor.stopMonitoring();
      }
      terminalSync.shutdown();
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