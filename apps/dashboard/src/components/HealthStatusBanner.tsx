/**
 * ============================================
 * HealthStatusBanner Component
 * ============================================
 * Displays backend connectivity status to users
 * Shows warning when backend is offline/unavailable
 * Provides retry functionality and auto-hides when online
 * ============================================
 */

import { useState, useEffect } from 'react';
import {
  Alert,
  Group,
  Text,
  Button,
  Box,
  Transition,
} from '@mantine/core';
import type { CSSProperties } from 'react';
import {
  IconAlertCircle,
  IconRefresh,
  IconWifi,
  IconWifiOff,
} from '@tabler/icons-react';
import type { BackendHealthStatus } from '../hooks/useBackendHealth';
import { useBackendHealth } from '../hooks/useBackendHealth';

export interface HealthStatusBannerProps {
  /**
   * Position of the banner
   * @default 'top'
   */
  position?: 'top' | 'bottom';

  /**
   * Allow user to dismiss the banner
   * @default true
   */
  dismissible?: boolean;

  /**
   * Show retry button
   * @default true
   */
  showRetry?: boolean;

  /**
   * Show response time when online
   * @default false
   */
  showResponseTime?: boolean;

  /**
   * Callback when banner is dismissed
   */
  onDismiss?: () => void;
}

/**
 * Banner component that displays backend health status
 *
 * @example
 * ```tsx
 * <HealthStatusBanner position="top" dismissible />
 * ```
 */
export function HealthStatusBanner({
  position = 'top',
  dismissible = true,
  showRetry = true,
  showResponseTime = false,
  onDismiss,
}: HealthStatusBannerProps) {
  const { status, error, responseTime, checkHealth } = useBackendHealth({
    pollInterval: 30000, // Check every 30 seconds
    enablePolling: true,
  });

  const [isDismissed, setIsDismissed] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  /**
   * Reset dismissed state when backend comes back online
   */
  useEffect(() => {
    if (status === 'online' && isDismissed) {
      setIsDismissed(false);
    }
  }, [status, isDismissed]);

  /**
   * Handle retry button click
   */
  const handleRetry = async () => {
    setIsRetrying(true);
    await checkHealth();
    setTimeout(() => setIsRetrying(false), 1000);
  };

  /**
   * Handle dismiss button click
   */
  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  /**
   * Determine banner visibility
   */
  const shouldShow = status === 'offline' && !isDismissed;

  /**
   * Get banner color based on status
   */
  const getColor = (status: BackendHealthStatus): string => {
    switch (status) {
      case 'online':
        return 'green';
      case 'offline':
        return 'red';
      case 'checking':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  /**
   * Get icon based on status
   */
  const getIcon = (status: BackendHealthStatus) => {
    switch (status) {
      case 'online':
        return <IconWifi size={rem(20)} />;
      case 'offline':
        return <IconWifiOff size={rem(20)} />;
      case 'checking':
        return <IconAlertCircle size={rem(20)} />;
      default:
        return <IconAlertCircle size={rem(20)} />;
    }
  };

  /**
   * Get status message
   */
  const getStatusMessage = (): string => {
    switch (status) {
      case 'online':
        return 'Backend is online';
      case 'offline':
        return error || 'Backend is currently unavailable. Running in limited mode.';
      case 'checking':
        return 'Checking backend connection...';
      default:
        return 'Unknown status';
    }
  };

  return (
    <Transition
      mounted={shouldShow}
      transition="slide-down"
      duration={300}
      timingFunction="ease"
    >
      {(styles: CSSProperties) => (
        <Box
          style={{
            ...styles,
            position: 'fixed',
            [position]: 0,
            left: 0,
            right: 0,
            zIndex: 1000,
            padding: rem(12),
          }}
        >
          <Alert
            variant="filled"
            color={getColor(status)}
            icon={getIcon(status)}
            withCloseButton={dismissible}
            onClose={dismissible ? handleDismiss : undefined}
            closeButtonLabel="Dismiss banner"
            styles={{
              root: {
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              },
            }}
          >
            <Group justify="space-between" wrap="nowrap">
              <Box style={{ flex: 1 }}>
                <Text size="sm" fw={600} mb={4}>
                  {getStatusMessage()}
                </Text>

                {status === 'offline' && (
                  <Text size="xs" style={{ opacity: 0.9 }}>
                    Some features may not be available. The dashboard will automatically
                    reconnect when the backend is back online.
                  </Text>
                )}

                {status === 'online' && showResponseTime && responseTime && (
                  <Text size="xs" style={{ opacity: 0.9 }}>
                    Response time: {responseTime}ms
                  </Text>
                )}
              </Box>

              {showRetry && status === 'offline' && (
                <Button
                  variant="white"
                  size="xs"
                  leftSection={<IconRefresh size={rem(14)} />}
                  onClick={handleRetry}
                  loading={isRetrying}
                  styles={{
                    root: {
                      color: 'var(--mantine-color-red-9)',
                    },
                  }}
                >
                  Retry
                </Button>
              )}
            </Group>
          </Alert>
        </Box>
      )}
    </Transition>
  );
}

export default HealthStatusBanner;
