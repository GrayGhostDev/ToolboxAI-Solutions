import * as React from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
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
import ErrorBoundary from "./components/ErrorBoundary";
// WebSocket removed - using Pusher for real-time features
import { pusherService } from "./services/pusher";
import { NetworkError } from "./components/ErrorComponents";
import { SessionMonitor, NetworkStatus } from "./components/auth/AuthRecovery";
// Import new Three.js infrastructure
import { ThreeProvider } from "./lib/three/ThreeProvider";
import { Scene3D } from "./lib/three/Scene3D";
import { FloatingCharactersV2 } from "./components/roblox/FloatingCharactersV2";
import { Canvas2D } from "./lib/three/fallbacks/Canvas2D";
import { PerformanceMonitor } from "./components/common/PerformanceMonitor";
// Import WebSocketProvider for context
import { WebSocketProvider } from "./contexts/WebSocketContext";

// Keep old FloatingCharacters as fallback
const FloatingCharacters = React.lazy(() => import("./components/roblox/FloatingCharacters").then(module => ({ default: module.FloatingCharacters })));

// Terminal services removed - not part of application
// Old performance monitor disabled due to performance issues

export default function App() {
  const role = useAppSelector((s) => s.user.role);
  const isAuthenticated = useAppSelector((s) => s.user.isAuthenticated);
  const loading = useAppSelector((s) => s.ui.loading);
  const [consentGiven, setConsentGiven] = React.useState(false);
  const [showConsent, setShowConsent] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Disable animations on Roblox Studio page to prevent movement
  const isRobloxPage = location.pathname.includes('/roblox-studio');

  // Initialize authentication and persistence
  useAuth();

  // Validate configuration on startup
  React.useEffect(() => {
    const validateConfig = async () => {
      // Dynamic import to avoid loading in production
      if (process.env.NODE_ENV === 'development') {
        const { configHealthCheck } = await import('./utils/configHealthCheck');
        const report = await configHealthCheck.runHealthCheck();

        if (report.overall === 'error') {
          console.error('❌ Critical configuration issues detected:', report);
          report.recommendations.forEach(rec => console.warn(`⚠️  ${rec}`));
        } else if (report.overall === 'warning') {
          console.warn('⚠️  Configuration warnings:', report);
        } else {
          console.log('✅ Configuration validated successfully');
        }
      }
    };

    validateConfig();
  }, []);

  // Initialize Pusher for real-time features
  React.useEffect(() => {
    let isConnected = false;

    if (isAuthenticated) {
      // Small delay to allow component to stabilize
      const connectTimer = setTimeout(() => {
        pusherService.connect();
        isConnected = true;
        console.log('✅ Pusher connected for real-time updates');
      }, 100);

      return () => {
        clearTimeout(connectTimer);
        // Only disconnect if we actually connected
        if (isConnected) {
          pusherService.disconnect();
        }
      };
    }
  }, [isAuthenticated]);

  // Lightweight performance monitoring for development
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 Lightweight performance monitoring enabled');
    }
  }, []);

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
      <WebSocketProvider autoConnect={true} debug={process.env.NODE_ENV === 'development'}>
        {/* Modern 3D Background with fallback support */}
        {!isRobloxPage && (
          <ThreeProvider fallback={<Canvas2D particleCount={30} animate={true} />}>
            <Scene3D>
              <FloatingCharactersV2
                characters={[
                  { type: 'astronaut', position: [-4, 2, -3] },
                  { type: 'robot', position: [4, 1, -2] },
                  { type: 'wizard', position: [0, 3, -4] },
                  { type: 'pirate', position: [-3, -1, -2] },
                  { type: 'ninja', position: [3, 0, -3] }
                ]}
                showStars={true}
                showClouds={true}
              />
            </Scene3D>
          </ThreeProvider>
        )}

        <AppLayout role={role} isRobloxPage={isRobloxPage}>
          <AppRoutes />
        </AppLayout>

        {/* Global Components */}
        <NotificationToast />
        <RealtimeToast />
        <SessionMonitor />
        <NetworkStatus />
        {loading && <LoadingOverlay />}

        {/* Performance Monitoring - Development Only */}
        <PerformanceMonitor enabled={process.env.NODE_ENV === 'development'} />

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