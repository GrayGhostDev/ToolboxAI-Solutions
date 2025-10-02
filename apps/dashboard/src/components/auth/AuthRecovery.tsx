/**
 * Auth Recovery Component
 *
 * Provides UI for automatic token refresh and session recovery
 */

import React, { useState, useEffect } from 'react';
import {
  Alert,
  Button,
  Loader,
  Modal,
  Progress,
  Text,
  Box,
  Stack,
  Notification,
} from '@mantine/core';
import {
  IconRefresh,
  IconLock,
  IconCheck,
  IconX,
  IconAlertTriangle,
} from '@tabler/icons-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { authSync } from '../../services/auth-sync';

interface AuthRecoveryProps {
  open: boolean;
  onClose: () => void;
  reason?: string;
}

export function AuthRecovery({ open, onClose, reason }: AuthRecoveryProps) {
  const [isRecovering, setIsRecovering] = useState(false);
  const [recoveryStatus, setRecoveryStatus] = useState<'idle' | 'recovering' | 'success' | 'failed'>('idle');
  const [progress, setProgress] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const [countdown, setCountdown] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = useAppSelector((state) => state.user.isAuthenticated);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (open && reason === 'token_expiring') {
      // Auto-start recovery for expiring tokens
      handleRecovery();
    }
  }, [open, reason]);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (countdown === 0 && recoveryStatus === 'failed' && retryCount < 3) {
      // Auto-retry after countdown
      handleRecovery();
    }
  }, [countdown, recoveryStatus, retryCount]);

  const handleRecovery = async () => {
    setIsRecovering(true);
    setRecoveryStatus('recovering');
    setProgress(0);
    setError(null);
    setRetryCount(prev => prev + 1);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90));
    }, 200);

    try {
      // Attempt token refresh
      await authSync.refreshToken();

      setProgress(100);
      setRecoveryStatus('success');
      clearInterval(progressInterval);

      // Auto-close after success
      setTimeout(() => {
        onClose();
        setRecoveryStatus('idle');
        setRetryCount(0);
      }, 2000);

    } catch (error: any) {
      clearInterval(progressInterval);
      setProgress(0);
      setRecoveryStatus('failed');
      setError(error.message || 'Recovery failed');

      // Set countdown for next retry
      if (retryCount < 3) {
        setCountdown(5 * retryCount); // Exponential backoff
      }
    } finally {
      setIsRecovering(false);
    }
  };

  const handleExtendSession = () => {
    authSync.extendSession();
    onClose();
  };

  const handleLogout = async () => {
    await authSync.logout();
    onClose();
  };

  const getReasonMessage = () => {
    switch (reason) {
      case 'token_expiring':
        return 'Your session is about to expire. Would you like to stay logged in?';
      case 'token_expired':
        return 'Your session has expired. Attempting to recover...';
      case 'refresh_failed':
        return 'Failed to refresh your session. Please try again.';
      case 'network_error':
        return 'Network connection lost. Attempting to reconnect...';
      default:
        return 'Session recovery needed.';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => {
        if (!isRecovering) {
          onClose();
        }
      }}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown={isRecovering}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Lock color="primary" />
        <Typography variant="h6">Session Recovery</Typography>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
          <Typography variant="body1" color="text.secondary">
            {getReasonMessage()}
          </Typography>

          {/* Recovery Status */}
          {recoveryStatus === 'recovering' && (
            <Box>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                <CircularProgress size={24} />
                <Typography variant="body2">
                  Refreshing your session...
                </Typography>
              </Stack>
              <LinearProgress variant="determinate" value={progress} />
            </Box>
          )}

          {recoveryStatus === 'success' && (
            <Alert
              severity="success"
              icon={<CheckCircle />}
            >
              Session recovered successfully!
            </Alert>
          )}

          {recoveryStatus === 'failed' && (
            <>
              <Alert
                severity="error"
                icon={<ErrorIcon />}
              >
                {error || 'Failed to recover session'}
              </Alert>

              {retryCount < 3 && countdown > 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Timer color="action" />
                  <Typography variant="body2" color="text.secondary">
                    Retrying in {countdown} seconds... (Attempt {retryCount}/3)
                  </Typography>
                </Box>
              )}
            </>
          )}

          {/* Session Info */}
          {reason === 'token_expiring' && (
            <Alert severity="warning">
              Your session will expire in 5 minutes due to inactivity.
              Click "Stay Logged In" to continue working.
            </Alert>
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        {reason === 'token_expiring' && recoveryStatus === 'idle' && (
          <>
            <Button
              onClick={handleLogout}
              color="secondary"
              disabled={isRecovering}
            >
              Logout
            </Button>
            <Button
              onClick={handleExtendSession}
              variant="contained"
              startIcon={<Refresh />}
              disabled={isRecovering}
            >
              Stay Logged In
            </Button>
          </>
        )}

        {(recoveryStatus === 'failed' || recoveryStatus === 'recovering') && (
          <>
            <Button
              onClick={handleLogout}
              color="secondary"
              disabled={isRecovering}
            >
              Logout
            </Button>
            <Button
              onClick={handleRecovery}
              variant="contained"
              startIcon={<Refresh />}
              disabled={isRecovering || countdown > 0}
            >
              {countdown > 0 ? `Wait ${countdown}s` : 'Retry'}
            </Button>
          </>
        )}

        {recoveryStatus === 'success' && (
          <Button
            onClick={onClose}
            variant="contained"
            color="success"
            startIcon={<CheckCircle />}
          >
            Continue
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

/**
 * Session Monitor Component
 * Shows session status and allows manual refresh
 */
export function SessionMonitor() {
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryReason, setRecoveryReason] = useState<string>('');

  useEffect(() => {
    const checkSession = () => {
      const info = authSync.getSessionInfo();
      setSessionInfo(info);

      if (info && info.isActive) {
        const now = Date.now();
        const inactiveTime = now - info.lastActivity;
        const inactiveMinutes = Math.floor(inactiveTime / 60000);

        // Show warning if approaching timeout
        if (inactiveMinutes >= 25 && inactiveMinutes < 30) {
          setRecoveryReason('token_expiring');
          setShowRecovery(true);
        }
      }
    };

    // Check session every minute
    const interval = setInterval(checkSession, 60000);
    checkSession(); // Initial check

    return () => clearInterval(interval);
  }, []);

  if (!sessionInfo || !sessionInfo.isActive) {
    return null;
  }

  const getSessionDuration = () => {
    const duration = Date.now() - sessionInfo.startTime;
    const hours = Math.floor(duration / 3600000);
    const minutes = Math.floor((duration % 3600000) / 60000);
    return `${hours}h ${minutes}m`;
  };

  const getInactiveTime = () => {
    const inactive = Date.now() - sessionInfo.lastActivity;
    const minutes = Math.floor(inactive / 60000);
    return `${minutes} min`;
  };

  return (
    <>
      <Box
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          bgcolor: 'background.paper',
          boxShadow: 1,
          borderRadius: 1,
          p: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          opacity: 0.9,
          '&:hover': {
            opacity: 1,
          },
        }}
      >
        <CheckCircle color="success" fontSize="small" />
        <Typography variant="caption" color="text.secondary">
          Session: {getSessionDuration()} | Inactive: {getInactiveTime()}
        </Typography>
        <Button
          size="small"
          onClick={() => authSync.extendSession()}
        >
          Extend
        </Button>
      </Box>

      <AuthRecovery
        open={showRecovery}
        onClose={() => setShowRecovery(false)}
        reason={recoveryReason}
      />
    </>
  );
}

/**
 * Network Status Monitor
 * Shows network connectivity status
 */
export function NetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showAlert, setShowAlert] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowAlert(true);
      setTimeout(() => setShowAlert(false), 3000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowAlert(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!showAlert) return null;

  return (
    <Notification
      onClose={() => setShowAlert(false)}
      color={isOnline ? 'green' : 'red'}
      title={isOnline ? 'Connection Restored' : 'Connection Lost'}
      style={{ position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)', zIndex: 1000 }}
    >
      {isOnline
        ? 'Connection restored. Your session is active.'
        : 'Network connection lost. Your work will be saved locally.'}
    </Notification>
  );
}

export default {
  AuthRecovery,
  SessionMonitor,
  NetworkStatus,
};
