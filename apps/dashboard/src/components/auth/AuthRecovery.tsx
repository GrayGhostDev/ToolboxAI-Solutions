/**
 * Auth Recovery Component (Migrated to Mantine v8)
 *
 * Provides UI for automatic token refresh and session recovery
 */

import React, { useState, useEffect } from 'react';
import {
  Alert,
  Button,
  Modal,
  Text,
  Box,
  Stack,
  Progress,
  Loader,
  Group,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconRefresh,
  IconLock,
  IconCircleCheck,
  IconAlertCircle,
  IconClock,
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
    <Modal
      opened={open}
      onClose={() => {
        if (!isRecovering) {
          onClose();
        }
      }}
      title={
        <Group gap="xs">
          <IconLock size={20} style={{ color: '#00bfff' }} />
          <Text size="lg" fw={600}>Session Recovery</Text>
        </Group>
      }
      size="md"
      closeOnEscape={!isRecovering}
    >
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          {getReasonMessage()}
        </Text>

        {/* Recovery Status */}
        {recoveryStatus === 'recovering' && (
          <Box>
            <Group gap="md" mb="sm">
              <Loader size="sm" />
              <Text size="sm">
                Refreshing your session...
              </Text>
            </Group>
            <Progress value={progress} color="blue" size="sm" />
          </Box>
        )}

        {recoveryStatus === 'success' && (
          <Alert
            icon={<IconCircleCheck size={20} />}
            color="green"
            title="Success"
          >
            Session recovered successfully!
          </Alert>
        )}

        {recoveryStatus === 'failed' && (
          <>
            <Alert
              icon={<IconAlertCircle size={20} />}
              color="red"
              title="Error"
            >
              {error || 'Failed to recover session'}
            </Alert>

            {retryCount < 3 && countdown > 0 && (
              <Group gap="xs">
                <IconClock size={16} />
                <Text size="sm" c="dimmed">
                  Retrying in {countdown} seconds... (Attempt {retryCount}/3)
                </Text>
              </Group>
            )}
          </>
        )}

        {/* Session Info */}
        {reason === 'token_expiring' && (
          <Alert color="yellow" title="Warning">
            Your session will expire in 5 minutes due to inactivity.
            Click "Stay Logged In" to continue working.
          </Alert>
        )}

        {/* Actions */}
        <Group justify="flex-end" mt="md">
          {reason === 'token_expiring' && recoveryStatus === 'idle' && (
            <>
              <Button
                onClick={handleLogout}
                variant="subtle"
                color="gray"
                disabled={isRecovering}
              >
                Logout
              </Button>
              <Button
                onClick={handleExtendSession}
                leftSection={<IconRefresh size={16} />}
                disabled={isRecovering}
                color="blue"
              >
                Stay Logged In
              </Button>
            </>
          )}

          {(recoveryStatus === 'failed' || recoveryStatus === 'recovering') && (
            <>
              <Button
                onClick={handleLogout}
                variant="subtle"
                color="gray"
                disabled={isRecovering}
              >
                Logout
              </Button>
              <Button
                onClick={handleRecovery}
                leftSection={<IconRefresh size={16} />}
                disabled={isRecovering || countdown > 0}
                color="blue"
              >
                {countdown > 0 ? `Wait ${countdown}s` : 'Retry'}
              </Button>
            </>
          )}

          {recoveryStatus === 'success' && (
            <Button
              onClick={onClose}
              color="green"
              leftSection={<IconCircleCheck size={16} />}
            >
              Continue
            </Button>
          )}
        </Group>
      </Stack>
    </Modal>
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
        style={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          backgroundColor: 'var(--mantine-color-body)',
          boxShadow: 'var(--mantine-shadow-sm)',
          borderRadius: 'var(--mantine-radius-sm)',
          padding: 'var(--mantine-spacing-sm)',
          opacity: 0.9,
        }}
      >
        <Group gap="xs">
          <IconCircleCheck size={16} color="var(--mantine-color-green-6)" />
          <Text size="xs" c="dimmed">
            Session: {getSessionDuration()} | Inactive: {getInactiveTime()}
          </Text>
          <Button
            size="xs"
            variant="subtle"
            onClick={() => authSync.extendSession()}
          >
            Extend
          </Button>
        </Group>
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

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      notifications.show({
        title: 'Connection Restored',
        message: 'Your session is active.',
        color: 'green',
        icon: <IconCircleCheck size={16} />,
        autoClose: 3000,
      });
    };

    const handleOffline = () => {
      setIsOnline(false);
      notifications.show({
        title: 'Connection Lost',
        message: 'Your work will be saved locally.',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
        autoClose: false,
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return null;
}

export default {
  AuthRecovery,
  SessionMonitor,
  NetworkStatus,
};
