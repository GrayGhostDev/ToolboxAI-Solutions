/**
 * Error UI Components
 *
 * Collection of user-friendly error components for different scenarios
 */

import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Collapse from '@mui/material/Collapse';
import Paper from '@mui/material/Paper';
import Skeleton from '@mui/material/Skeleton';
import Fade from '@mui/material/Fade';
import Zoom from '@mui/material/Zoom';
import { useTheme } from '@mui/material/styles';
import Container from '@mui/material/Container';
import Link from '@mui/material/Link';

import {
  WifiOff,
  CloudOff,
  ErrorOutline,
  Refresh,
  Close,
  CheckCircle,
  Info,
  Warning,
  ArrowBack,
  Home,
  Support,
  Timer,
  TrendingUp,
} from '@mui/icons-material';

/**
 * Network Error Component
 * Shows when there's no internet connection
 */
export function NetworkError({
  onRetry,
  message = "Unable to connect to the server",
}: {
  onRetry?: () => void;
  message?: string;
}) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline as EventListener);
    window.addEventListener("offline", handleOffline as EventListener);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <Card sx={{ maxWidth: 400, mx: 'auto', my: 4 }}>
      <CardContent sx={{ textAlign: 'center', py: 4 }}>
        <WifiOff sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Connection Problem
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          {message}
        </Typography>

        {!isOnline && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            You appear to be offline. Please check your internet connection.
          </Alert>
        )}

        {isOnline && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Your internet connection is restored. Try refreshing.
          </Alert>
        )}

        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={(e: React.MouseEvent) => onRetry}
          disabled={!isOnline}
          fullWidth
        >
          {isOnline ? 'Retry Connection' : 'Waiting for Connection...'}
        </Button>
      </CardContent>
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
  const theme = useTheme();

  const getErrorMessage = () => {
    if (error?.response?.status === 404) return "The requested resource was not found";
    if (error?.response?.status === 403) return "You don't have permission to access this resource";
    if (error?.response?.status === 401) return "Your session has expired. Please log in again";
    if (error?.response?.status >= 500) return "Server error. Please try again later";
    return error?.message || "An unexpected error occurred";
  };

  const getErrorTitle = () => {
    if (error?.response?.status === 404) return "Not Found";
    if (error?.response?.status === 403) return "Access Denied";
    if (error?.response?.status === 401) return "Authentication Required";
    if (error?.response?.status >= 500) return "Server Error";
    return "Error";
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        borderLeft: 4,
        borderColor: 'error.main',
        bgcolor: theme.palette.mode === 'dark' ? 'error.dark' : 'error.lighter',
      }}
    >
      <Stack spacing={2}>
        <Stack direction="row" alignItems="center" spacing={2}>
          <ErrorOutline color="error" />
          <Box flex={1}>
            <Typography variant="h6" color="error">
              {getErrorTitle()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {getErrorMessage()}
            </Typography>
          </Box>
        </Stack>

        {retryCount > 0 && (
          <LinearProgress
            variant="determinate"
            value={(retryCount / maxRetries) * 100}
            sx={{ height: 6, borderRadius: 1 }}
          />
        )}

        {retryCount > 0 && (
          <Typography variant="caption" color="text.secondary">
            Retry attempt {retryCount} of {maxRetries}
          </Typography>
        )}

        <Stack direction="row" spacing={2}>
          {onRetry && retryCount < maxRetries && (
            <Button
              variant="contained"
              size="small"
              startIcon={<Refresh />}
              onClick={(e: React.MouseEvent) => onRetry}
            >
              Try Again
            </Button>
          )}

          {showDetails && error?.response && (
            <Button
              variant="outlined"
              size="small"
              onClick={(e: React.MouseEvent) => () => setExpanded(!expanded)}
            >
              {expanded ? 'Hide' : 'Show'} Details
            </Button>
          )}
        </Stack>

        <Collapse in={expanded}>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.paper' }}>
            <Typography variant="caption" component="pre" sx={{ fontFamily: 'monospace' }}>
              {JSON.stringify(error?.response?.data || error, null, 2)}
            </Typography>
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
  title = "Failed to Load",
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
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Stack spacing={3} alignItems="center" textAlign="center">
        <CloudOff sx={{ fontSize: 80, color: 'text.secondary' }} />

        <Box>
          <Typography variant="h5" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {message}
          </Typography>
        </Box>

        <Stack direction="row" spacing={2}>
          {showBackButton && onGoBack && (
            <Button
              variant="outlined"
              startIcon={<ArrowBack />}
              onClick={(e: React.MouseEvent) => onGoBack}
            >
              Go Back
            </Button>
          )}

          {onRetry && (
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={(e: React.MouseEvent) => onRetry}
            >
              Try Again
            </Button>
          )}
        </Stack>
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

  return (
    <Fade in>
      <Alert
        severity={severity}
        action={
          onDismiss && (
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={(e: React.MouseEvent) => onDismiss}
            >
              <Close fontSize="inherit" />
            </IconButton>
          )
        }
        sx={{ mt: 1 }}
      >
        {message}
      </Alert>
    </Fade>
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
  message = "Retrying in",
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
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" spacing={2}>
        <CircularProgress
          variant="determinate"
          value={(timeLeft / seconds) * 100}
          size={40}
        />
        <Box flex={1}>
          <Typography variant="body2">
            {message} {timeLeft} seconds...
          </Typography>
        </Box>
        {onCancel && (
          <Button size="small" onClick={(e: React.MouseEvent) => onCancel}>
            Cancel
          </Button>
        )}
      </Stack>
    </Paper>
  );
}

/**
 * Empty State Error Component
 * Shows when no data is available
 */
export function EmptyState({
  title = "No Data Available",
  message = "There's nothing to show here yet",
  icon = <Info />,
  action,
}: {
  title?: string;
  message?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <Box
      sx={{
        py: 8,
        px: 3,
        textAlign: 'center',
        color: 'text.secondary',
      }}
    >
      <Box sx={{ mb: 3, opacity: 0.5 }}>
        {React./* TODO: React 19 - Review usage of cloneElement */ cloneElement(icon as React.ReactElement, {
          sx: { fontSize: 80 },
        })}
      </Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" paragraph>
        {message}
      </Typography>
      {action && <Box sx={{ mt: 3 }}>{action}</Box>}
    </Box>
  );
}

/**
 * Success Recovery Component
 * Shows when error is successfully recovered
 */
export function SuccessRecovery({
  message = "Connection restored successfully",
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
    <Zoom in>
      <Alert
        severity="success"
        icon={<CheckCircle />}
        action={
          onDismiss && (
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={(e: React.MouseEvent) => onDismiss}
            >
              <Close fontSize="inherit" />
            </IconButton>
          )
        }
      >
        {message}
      </Alert>
    </Zoom>
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
    <Box sx={{ p: 2 }}>
      {showAvatar && (
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <Skeleton variant="circular" width={40} height={40} />
          <Box flex={1}>
            <Skeleton variant="text" width="30%" />
            <Skeleton variant="text" width="20%" />
          </Box>
        </Stack>
      )}
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          variant="text"
          width={`${Math.random() * 30 + 70}%`}
          sx={{ mb: 1 }}
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