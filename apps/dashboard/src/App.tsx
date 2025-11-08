import * as React from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { LoadingOverlay } from '@mantine/core';
import AppLayout from './components/layout/AppLayout';
import { useAppSelector } from './store';
import AppRoutes from './routes';
import { ConsentModal } from './components/modals/ConsentModal';
import { NotificationToast } from './components/notifications/NotificationToast';
import { logger } from './utils/logger';
import RealtimeToast from './components/notifications/RealtimeToast';
import { COPPA_COMPLIANCE } from './config';
// Auth Components
import ClerkLogin from './components/auth/ClerkLogin';
import ClerkSignUp from './components/auth/ClerkSignUp';
import Login from './components/pages/Login';
import Register from './components/pages/Register';
import PasswordReset from './components/pages/PasswordReset';

// Unified Auth Hook
import { useUnifiedAuth } from './hooks/useUnifiedAuth';
import ErrorBoundary from './components/ErrorBoundary';
// Role-Based Router
import { RoleBasedRouter } from './components/auth/RoleBasedRouter';
// WebSocket removed - using Pusher for real-time features
import { pusherService } from './services/pusher';
import { PusherProvider } from './contexts/PusherContext';
import { SessionMonitor, NetworkStatus } from './components/auth/AuthRecovery';
// Backend Health Monitoring
import { HealthStatusBanner } from './components/HealthStatusBanner';
// Lazy load heavy 3D components to improve initial load time
const ThreeProvider = React.lazy(() => import('./components/three/ThreeProvider').then(m => ({ default: m.ThreeProvider })));
const Scene3D = React.lazy(() => import('./components/three/Scene3D').then(m => ({ default: m.Scene3D })));
const FloatingCharactersV2 = React.lazy(() => import('./components/roblox/FloatingCharactersV2').then(m => ({ default: m.FloatingCharactersV2 })));
const Canvas2D = React.lazy(() => import('./components/three/fallbacks/Canvas2D').then(m => ({ default: m.Canvas2D })));
const PerformanceMonitor = React.lazy(() => import('./components/common/PerformanceMonitor').then(m => ({ default: m.PerformanceMonitor })));

// Development tools - lazy loaded
const MigrationControlPanel = React.lazy(() => import('./components/migration/MigrationWrapper').then(m => ({ default: m.MigrationControlPanel })));
const RoutePerformanceMonitor = React.lazy(() => import('./components/performance/RoutePerformanceMonitor').then(m => ({ default: m.RoutePerformanceMonitor })));
const RoutePreloader = React.lazy(() => import('./components/performance/RoutePreloader').then(m => ({ default: m.RoutePreloader })));

// Keep old FloatingCharacters as fallback (currently unused, may be used for feature flag)
const _FloatingCharacters = React.lazy(() => import('./components/roblox/FloatingCharacters').then(module => ({ default: module.FloatingCharacters })));

// Cookie banner - only in production
const CookieBannerLazy = React.lazy(() => import('./components/consent/CookieBanner').then(m => ({ default: m.default })));

// Command Palette for quick navigation
import { CommandPalette } from './components/navigation/CommandPalette';
// Development Tools
import { DevRoleSwitcher } from './components/dev/DevRoleSwitcher';

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

  // Check if Clerk auth is enabled
  const useClerkAuthEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';

  // Check for bypass mode
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';

  // Use the unified auth hook that handles conditional logic correctly
  const _authHookResult = useUnifiedAuth();

  // Validate configuration on startup (disabled by default to reduce console noise)
  // Enable with VITE_ENABLE_CONFIG_VALIDATION=true if needed
  React.useEffect(() => {
    const validateConfig = async () => {
      // Only run if explicitly enabled
      if (process.env.NODE_ENV === 'development' && import.meta.env.VITE_ENABLE_CONFIG_VALIDATION === 'true') {
        const { configHealthCheck } = await import('./utils/configHealthCheck');
        const report = await configHealthCheck.runHealthCheck();

        // Only warn once in dev mode to avoid duplicate logs in StrictMode
        if (report.overall === 'error') {
          logger.error('Critical configuration issues detected', report);
          report.recommendations.forEach(rec => logger.warn(rec));
        } else if (report.overall === 'warning' && !('__configWarned' in window)) {
          logger.warn('Configuration warnings detected', report);
          (window as any).__configWarned = true; // Mark that we've warned
        } else if (report.overall === 'healthy') {
          logger.info('Configuration validated successfully');
        }
      }
    };

    validateConfig();
  }, []);

  // Initialize Pusher for real-time features
  React.useEffect(() => {
    let isConnected = false;

    if (isAuthenticated && !bypassAuth) {
      // Small delay to allow component to stabilize
      const connectTimer = setTimeout(() => {
        pusherService.connect();
        isConnected = true;
        logger.info('Pusher connected for real-time updates');
      }, 100);

      return () => {
        clearTimeout(connectTimer);
        // Only disconnect if we actually connected
        if (isConnected) {
          pusherService.disconnect();
        }
      };
    }
    return undefined; // Explicit return for when not authenticated
  }, [isAuthenticated, bypassAuth]);

  // Lightweight performance monitoring for development
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      logger.debug('Lightweight performance monitoring enabled');
    }
  }, []);

  React.useEffect(() => {
    // Check if COPPA consent is needed
    if (COPPA_COMPLIANCE && role === 'student' && !consentGiven) {
      const consent = localStorage.getItem('coppa_consent');
      if (!consent) {
        setShowConsent(true);
      } else {
        setConsentGiven(true);
      }
    }
  }, [role, consentGiven]);

  const handleConsentClose = (accepted: boolean) => {
    if (accepted) {
      localStorage.setItem('coppa_consent', 'true');
      setConsentGiven(true);
      // Navigate to dashboard after consent is accepted
      navigate('/dashboard');
    }
    setShowConsent(false);
  };

  // Check if we're in development mode
  const isDevelopment = import.meta.env.VITE_ENV === 'development' || process.env.NODE_ENV === 'development';

  // If not authenticated and not bypassing auth, show auth routes
  if (!isAuthenticated && !bypassAuth) {
    return (
      <ErrorBoundary>
        <Routes>
          {/* Use Clerk components if enabled, otherwise use legacy */}
          <Route path="/login" element={useClerkAuthEnabled ? <ClerkLogin /> : <Login />} />
          <Route path="/sign-in" element={<ClerkLogin />} />
          <Route path="/register" element={useClerkAuthEnabled ? <ClerkSignUp /> : <Register />} />
          <Route path="/sign-up" element={<ClerkSignUp />} />
          <Route path="/password-reset" element={<PasswordReset />} />
          <Route path="*" element={<Navigate to={useClerkAuthEnabled ? '/sign-in' : '/login'} replace />} />
        </Routes>

        {/* Global Components */}
        <NotificationToast />
        {loading && <LoadingOverlay visible={loading} />}
      </ErrorBoundary>
    );
  }

  // Log development mode status
  if (bypassAuth && isDevelopment) {
    logger.info('Development mode: Authentication bypassed');
  }

  return (
    <ErrorBoundary>
      <PusherProvider
        autoConnect={!bypassAuth}
        enablePresence={!bypassAuth}
        debug={process.env.NODE_ENV === 'development' && !bypassAuth}
        onConnectionChange={(state) => !bypassAuth && logger.debug('Pusher connection state:', state)}
      >
        {/* Modern 3D Background with fallback support - lazy loaded */}
        {!isRobloxPage && !bypassAuth && (
          <React.Suspense fallback={<div style={{ position: 'fixed', inset: 0, background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', zIndex: -1, pointerEvents: 'none' }} />}>
            <ThreeProvider fallback={
              <React.Suspense fallback={null}>
                <Canvas2D particleCount={30} animate={true} />
              </React.Suspense>
            }>
              <React.Suspense fallback={null}>
                <Scene3D>
                  <React.Suspense fallback={null}>
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
                  </React.Suspense>
                </Scene3D>
              </React.Suspense>
            </ThreeProvider>
          </React.Suspense>
        )}

        {/* Simple background for bypass mode */}
        {!isRobloxPage && bypassAuth && (
          <div style={{
            position: 'fixed',
            inset: 0,
            background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            zIndex: -1,
            pointerEvents: 'none'
          }} />
        )}

        <AppLayout role={role} isRobloxPage={isRobloxPage}>
          <RoleBasedRouter>
            <AppRoutes />
          </RoleBasedRouter>
        </AppLayout>

        {/* Global Components */}
        <HealthStatusBanner position="top" dismissible showRetry />
        <CommandPalette />
        <NotificationToast />
        <RealtimeToast />
        {/* Disable complex session monitoring in development */}
        {!bypassAuth && <SessionMonitor />}
        {!bypassAuth && <NetworkStatus />}
        {loading && <LoadingOverlay visible={loading} />}

        {/* Cookie Consent */}
        {process.env.NODE_ENV === 'production' && (
          <React.Suspense fallback={null}>
            <CookieBannerLazy />
          </React.Suspense>
        )}

        {/* Performance Monitoring - Development Only */}
        {process.env.NODE_ENV === 'development' && (
          <React.Suspense fallback={null}>
            <PerformanceMonitor enabled={true} />
          </React.Suspense>
        )}

        {/* Role Switcher - Development Only */}
        {process.env.NODE_ENV === 'development' && !bypassAuth && (
          <DevRoleSwitcher />
        )}

        {/* COPPA Consent Modal */}
        {showConsent && (
          <ConsentModal
            opened={showConsent}
            onClose={handleConsentClose}
          />
        )}

        {/* Development Tools - Lazy Loaded */}
        {process.env.NODE_ENV === 'development' && (
          <React.Suspense fallback={null}>
            <MigrationControlPanel />
          </React.Suspense>
        )}

        {/* Performance Tools - Development Only */}
        {process.env.NODE_ENV === 'development' && (
          <>
            <React.Suspense fallback={null}>
              <RoutePerformanceMonitor
                enabled={true}
                timeoutThreshold={1500}
              />
            </React.Suspense>
            <React.Suspense fallback={null}>
              <RoutePreloader
                enabled={true}
                aggressivePreload={false}
              />
            </React.Suspense>
          </>
        )}
      </PusherProvider>
    </ErrorBoundary>
  );
}