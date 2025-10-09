/**
 * Error UI Components
 *
 * Collection of user-friendly error components for different scenarios
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  Text,
  Alert,
  Loader,
  Progress,
  Stack,
  ActionIcon,
  Collapse,
  Paper,
  Skeleton,
  Transition,
  useMantineTheme,
  Container,
  Anchor,
  Group,
} from '@mantine/core';
import {
  IconWifiOff,
  IconCloudOff,
  IconExclamationCircle,
  IconRefresh,
  IconX,
  IconCircleCheck,
  IconInfoCircle,
  IconAlertTriangle,
  IconArrowLeft,
  IconHome,
  IconHelp,
  IconClock,
  IconTrendingUp,
} from '@tabler/icons-react';

/**
 * Network Error Component
 * Shows when there's no internet connection
 */
export function NetworkError({
  onRetry,
  message = 'Unable to connect to the server',
}: {
  onRetry?: () => void;
  message?: string;
}) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <Card
      style={{ maxWidth: 400, margin: '2rem auto' }}
      p="xl"
      ta="center"
    >
      <IconWifiOff size={64} color="var(--mantine-color-red-6)" style={{ marginBottom: 16 }} />
      <Text size="xl" fw={600} mb="sm">
        Connection Problem
      </Text>
      <Text size="sm" c="dimmed" mb="md">
        {message}
      </Text>

      {!isOnline && (
        <Alert
          icon={<IconAlertTriangle size="1rem" />}
          color="yellow"
          mb="md"
        >
          You appear to be offline. Please check your internet connection.
        </Alert>
      )}

      {isOnline && (
        <Alert
          icon={<IconInfoCircle size="1rem" />}
          color="blue"
          mb="md"
        >
          Your internet connection is restored. Try refreshing.
        </Alert>
      )}

      <Button
        leftSection={<IconRefresh size="1rem" />}
        onClick={onRetry}
        disabled={!isOnline}
        fullWidth
      >
        {isOnline ? 'Retry Connection' : 'Waiting for Connection...'}
      </Button>
    </Card>
  );
}

/**
 * API Error Component
 * Shows when an API call fails
 */
export function ApiError({
  error,
  onRetry,
  retryCount = 0,
  maxRetries = 3,
  showDetails = false,
}: {
  error: any;
  onRetry?: () => void;
  retryCount?: number;
  maxRetries?: number;
  showDetails?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const theme = useMantineTheme();

  const getErrorMessage = () => {
    if (error?.response?.status === 404) return 'The requested resource was not found';
    if (error?.response?.status === 403) return "You don't have permission to access this resource";
    if (error?.response?.status === 401) return 'Your session has expired. Please log in again';
    if (error?.response?.status >= 500) return 'Server error. Please try again later';
    return error?.message || 'An unexpected error occurred';
  };

  const getErrorTitle = () => {
    if (error?.response?.status === 404) return 'Not Found';
    if (error?.response?.status === 403) return 'Access Denied';
    if (error?.response?.status === 401) return 'Authentication Required';
    if (error?.response?.status >= 500) return 'Server Error';
    return 'Error';
  };

  return (
    <Paper
      p="lg"
      style={{
        borderLeft: `4px solid ${theme.colors.red[6]}`,
        backgroundColor: theme.colorScheme === 'dark' ? theme.colors.red[9] : theme.colors.red[0],
      }}
    >
      <Stack gap="md">
        <Group>
          <IconExclamationCircle color={theme.colors.red[6]} />
          <Box style={{ flex: 1 }}>
            <Text size="lg" fw={600} c="red.6">
              {getErrorTitle()}
            </Text>
            <Text size="sm" c="dimmed">
              {getErrorMessage()}
            </Text>
          </Box>
        </Group>

        {retryCount > 0 && (
          <Progress
            value={(retryCount / maxRetries) * 100}
            size="sm"
            radius="sm"
          />
        )}

        {retryCount > 0 && (
          <Text size="xs" c="dimmed">
            Retry attempt {retryCount} of {maxRetries}
          </Text>
        )}

        <Group>
          {onRetry && retryCount < maxRetries && (
            <Button
              size="sm"
              leftSection={<IconRefresh size="1rem" />}
              onClick={onRetry}
            >
              Try Again
            </Button>
          )}

          {showDetails && error?.response && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Hide' : 'Show'} Details
            </Button>
          )}
        </Group>

        <Collapse in={expanded}>
          <Paper p="md" withBorder>
            <Text
              component="pre"
              size="xs"
              style={{ fontFamily: 'monospace', overflow: 'auto' }}
            >
              {JSON.stringify(error?.response?.data || error, null, 2)}
            </Text>
          </Paper>
        </Collapse>
      </Stack>
    </Paper>
  );
}

/**
 * Loading Error Component
 * Shows when data fails to load with retry capability
 */
export function LoadingError({
  title = 'Failed to Load',
  message = "We couldn't load the data you requested",
  onRetry,
  onGoBack,
  showBackButton = true,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  onGoBack?: () => void;
  showBackButton?: boolean;
}) {
  return (
    <Container size="sm" py="xl">
      <Stack gap="lg" align="center" ta="center">
        <IconCloudOff size={80} color="var(--mantine-color-dimmed)" />

        <Box>
          <Text size="xl" fw={600} mb="sm">
            {title}
          </Text>
          <Text size="md" c="dimmed">
            {message}
          </Text>
        </Box>

        <Group>
          {showBackButton && onGoBack && (
            <Button
              variant="outline"
              leftSection={<IconArrowLeft size="1rem" />}
              onClick={onGoBack}
            >
              Go Back
            </Button>
          )}

          {onRetry && (
            <Button
              leftSection={<IconRefresh size="1rem" />}
              onClick={onRetry}
            >
              Try Again
            </Button>
          )}
        </Group>
      </Stack>
    </Container>
  );
}

/**
 * Inline Error Component
 * Small error message for form fields or inline content
 */
export function InlineError({
  message,
  onDismiss,
  severity = 'error',
}: {
  message: string;
  onDismiss?: () => void;
  severity?: 'error' | 'warning' | 'info';
}) {
  if (!message) return null;

  const getColor = () => {
    switch (severity) {
      case 'warning': return 'yellow';
      case 'info': return 'blue';
      default: return 'red';
    }
  };

  const getIcon = () => {
    switch (severity) {
      case 'warning': return <IconAlertTriangle size="1rem" />;
      case 'info': return <IconInfoCircle size="1rem" />;
      default: return <IconExclamationCircle size="1rem" />;
    }
  };

  return (
    <Transition mounted={true} transition="fade" duration={200}>
      {(styles) => (
        <Alert
          icon={getIcon()}
          color={getColor()}
          mt="xs"
          style={styles}
          onClose={onDismiss}
          withCloseButton={!!onDismiss}
        >
          {message}
        </Alert>
      )}
    </Transition>
  );
}

/**
 * Retry Timer Component
 * Shows countdown until automatic retry
 */
export function RetryTimer({
  seconds,
  onRetry,
  onCancel,
  message = 'Retrying in',
}: {
  seconds: number;
  onRetry: () => void;
  onCancel?: () => void;
  message?: string;
}) {
  const [timeLeft, setTimeLeft] = useState(seconds);

  useEffect(() => {
    if (timeLeft <= 0) {
      onRetry();
      return;
    }

    const timer = setTimeout(() => {
      setTimeLeft(timeLeft - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [timeLeft, onRetry]);

  return (
    <Paper p="md">
      <Group>
        <Loader
          variant="ring"
          size={40}
        />
        <Box style={{ flex: 1 }}>
          <Text size="sm">
            {message} {timeLeft} seconds...
          </Text>
        </Box>
        {onCancel && (
          <Button size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </Group>
    </Paper>
  );
}

/**
 * Empty State Error Component
 * Shows when no data is available
 */
export function EmptyState({
  title = 'No Data Available',
  message = "There's nothing to show here yet",
  icon = <IconInfoCircle />,
  action,
}: {
  title?: string;
  message?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <Box
      py="xl"
      px="lg"
      ta="center"
      c="dimmed"
    >
      <Box mb="lg" style={{ opacity: 0.5 }}>
        {React.cloneElement(icon as React.ReactElement, {
          size: 80,
        })}
      </Box>
      <Text size="lg" fw={600} mb="sm">
        {title}
      </Text>
      <Text size="sm" mb="md">
        {message}
      </Text>
      {action && <Box mt="lg">{action}</Box>}
    </Box>
  );
}

/**
 * Success Recovery Component
 * Shows when error is successfully recovered
 */
export function SuccessRecovery({
  message = 'Connection restored successfully',
  onDismiss,
}: {
  message?: string;
  onDismiss?: () => void;
}) {
  useEffect(() => {
    if (onDismiss) {
      const timer = setTimeout(onDismiss, 3000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [onDismiss]);

  return (
    <Transition mounted={true} transition="scale" duration={300}>
      {(styles) => (
        <Alert
          icon={<IconCircleCheck size="1rem" />}
          color="green"
          style={styles}
          onClose={onDismiss}
          withCloseButton={!!onDismiss}
        >
          {message}
        </Alert>
      )}
    </Transition>
  );
}

/**
 * Error Skeleton Component
 * Shows loading skeleton when retrying
 */
export function ErrorSkeleton({
  lines = 3,
  showAvatar = false,
}: {
  lines?: number;
  showAvatar?: boolean;
}) {
  return (
    <Box p="md">
      {showAvatar && (
        <Group mb="md">
          <Skeleton height={40} circle />
          <Box style={{ flex: 1 }}>
            <Skeleton height={8} width="30%" mb="xs" />
            <Skeleton height={8} width="20%" />
          </Box>
        </Group>
      )}
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          height={8}
          width={`${Math.random() * 30 + 70}%`}
          mb="xs"
        />
      ))}
    </Box>
  );
}

/**
 * Hook for managing error states
 */
export function useErrorHandler() {
  const [error, setError] = useState<Error | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const handleError = (error: Error) => {
    setError(error);
    console.error('Error handled:', error);
  };

  const clearError = () => {
    setError(null);
    setRetryCount(0);
  };

  const retry = async (callback: () => Promise<any>) => {
    setIsRetrying(true);
    setRetryCount(prev => prev + 1);

    try {
      const result = await callback();
      clearError();
      return result;
    } catch (err) {
      handleError(err as Error);
      throw err;
    } finally {
      setIsRetrying(false);
    }
  };

  return {
    error,
    isRetrying,
    retryCount,
    handleError,
    clearError,
    retry,
  };
}

export default {
  NetworkError,
  ApiError,
  LoadingError,
  InlineError,
  RetryTimer,
  EmptyState,
  SuccessRecovery,
  ErrorSkeleton,
  useErrorHandler,
};