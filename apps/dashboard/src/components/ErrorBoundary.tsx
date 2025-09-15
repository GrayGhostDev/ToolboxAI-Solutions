/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the component tree,
 * logs errors, and displays a fallback UI
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Alert,
  AlertTitle,
  Stack,
  Collapse,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  useTheme,
  Link,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh,
  ExpandMore,
  ExpandLess,
  Home,
  BugReport,
  ContentCopy,
  Check,
} from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'page' | 'section' | 'component';
  showDetails?: boolean;
  enableRecovery?: boolean;
  enableReporting?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
  showDetails: boolean;
  copied: boolean;
  isRecovering: boolean;
}

/**
 * Error Boundary Class Component
 * (Must be a class component as of React 18)
 */
export class ErrorBoundary extends Component<Props, State> {
  private resetTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      showDetails: false,
      copied: false,
      isRecovering: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error Boundary caught an error:', error, errorInfo);
    }

    // Update state with error details
    this.setState(prevState => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report to error tracking service (e.g., Sentry)
    if (this.props.enableReporting) {
      this.reportError(error, errorInfo);
    }

    // Auto-recovery attempt after multiple errors
    if (this.props.enableRecovery && this.state.errorCount >= 3) {
      this.scheduleReset();
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  /**
   * Report error to tracking service
   */
  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // In production, this would send to Sentry, LogRocket, etc.
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      level: this.props.level || 'component',
    };

    // Log to console for now
    console.log('Error Report:', errorReport);

    // TODO: Send to actual error tracking service
    // window.Sentry?.captureException(error, { extra: errorReport });
  };

  /**
   * Reset error boundary state
   */
  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
      copied: false,
      isRecovering: false,
    });
  };

  /**
   * Schedule automatic reset
   */
  private scheduleReset = () => {
    this.setState({ isRecovering: true });
    this.resetTimeoutId = setTimeout(() => {
      this.handleReset();
    }, 5000);
  };

  /**
   * Copy error details to clipboard
   */
  private handleCopyError = () => {
    const { error, errorInfo } = this.state;
    const errorText = `
Error: ${error?.message}
Stack: ${error?.stack}
Component Stack: ${errorInfo?.componentStack}
Time: ${new Date().toISOString()}
URL: ${window.location.href}
    `.trim();

    navigator.clipboard.writeText(errorText);
    this.setState({ copied: true });
    setTimeout(() => this.setState({ copied: false }), 2000);
  };

  /**
   * Navigate to home page
   */
  private handleGoHome = () => {
    window.location.href = '/';
  };

  /**
   * Toggle error details visibility
   */
  private toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails,
    }));
  };

  render() {
    const { hasError, error, errorInfo, showDetails, copied, isRecovering, errorCount } = this.state;
    const { children, fallback, level = 'component', showDetails: showDetailsProp = true } = this.props;

    if (hasError && error) {
      // Custom fallback provided
      if (fallback) {
        return <>{fallback}</>;
      }

      // Default error UI based on level
      return (
        <ErrorFallback
          error={error}
          errorInfo={errorInfo}
          level={level}
          showDetails={showDetails || false}
          showDetailsProp={showDetailsProp}
          onToggleDetails={this.toggleDetails}
          onReset={this.handleReset}
          onCopy={this.handleCopyError}
          onGoHome={this.handleGoHome}
          copied={copied}
          isRecovering={isRecovering}
          errorCount={errorCount}
        />
      );
    }

    return children;
  }
}

/**
 * Error Fallback UI Component
 */
interface ErrorFallbackProps {
  error: Error;
  errorInfo: ErrorInfo | null;
  level: 'page' | 'section' | 'component';
  showDetails: boolean;
  showDetailsProp: boolean;
  onToggleDetails: () => void;
  onReset: () => void;
  onCopy: () => void;
  onGoHome: () => void;
  copied: boolean;
  isRecovering: boolean;
  errorCount: number;
}

function ErrorFallback({
  error,
  errorInfo,
  level,
  showDetails,
  showDetailsProp,
  onToggleDetails,
  onReset,
  onCopy,
  onGoHome,
  copied,
  isRecovering,
  errorCount,
}: ErrorFallbackProps) {
  const theme = useTheme();

  // Different layouts based on error level
  if (level === 'page') {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            borderTop: 4,
            borderColor: 'error.main',
          }}
        >
          <ErrorIcon
            sx={{
              fontSize: 80,
              color: 'error.main',
              mb: 2,
            }}
          />

          <Typography variant="h4" gutterBottom>
            Oops! Something went wrong
          </Typography>

          <Typography variant="body1" color="text.secondary" paragraph>
            We're sorry, but something unexpected happened. The error has been logged
            and we'll look into it.
          </Typography>

          {errorCount >= 3 && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              Multiple errors detected. The page may be unstable.
            </Alert>
          )}

          <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 3 }}>
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={onReset}
              disabled={isRecovering}
            >
              {isRecovering ? 'Recovering...' : 'Try Again'}
            </Button>

            <Button
              variant="outlined"
              startIcon={<Home />}
              onClick={onGoHome}
            >
              Go to Homepage
            </Button>
          </Stack>

          {showDetailsProp && (
            <>
              <Button
                size="small"
                onClick={onToggleDetails}
                endIcon={showDetails ? <ExpandLess /> : <ExpandMore />}
              >
                {showDetails ? 'Hide' : 'Show'} Technical Details
              </Button>

              <Collapse in={showDetails}>
                <Box sx={{ mt: 3, textAlign: 'left' }}>
                  <Alert severity="error" sx={{ mb: 2 }}>
                    <AlertTitle>Error Message</AlertTitle>
                    <Typography variant="body2" fontFamily="monospace">
                      {error.message}
                    </Typography>
                  </Alert>

                  {error.stack && (
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.100' }}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle2" gutterBottom>
                          Stack Trace
                        </Typography>
                        <IconButton size="small" onClick={onCopy}>
                          {copied ? <Check color="success" /> : <ContentCopy />}
                        </IconButton>
                      </Stack>
                      <Typography
                        variant="body2"
                        component="pre"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          overflow: 'auto',
                          maxHeight: 200,
                        }}
                      >
                        {error.stack}
                      </Typography>
                    </Paper>
                  )}
                </Box>
              </Collapse>
            </>
          )}
        </Paper>
      </Container>
    );
  }

  // Inline error for sections and components
  return (
    <Box
      sx={{
        p: level === 'section' ? 3 : 2,
        border: 1,
        borderColor: 'error.main',
        borderRadius: 1,
        bgcolor: 'error.lighter',
      }}
    >
      <Stack direction="row" spacing={2} alignItems="center">
        <ErrorIcon color="error" />
        <Box flex={1}>
          <Typography variant="subtitle1" color="error">
            {level === 'section' ? 'Section Error' : 'Component Error'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {error.message}
          </Typography>
        </Box>
        <Button
          size="small"
          variant="outlined"
          onClick={onReset}
          disabled={isRecovering}
        >
          Retry
        </Button>
      </Stack>
    </Box>
  );
}

/**
 * Higher-order component to wrap components with error boundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

/**
 * Hook for error recovery and retry logic
 */
export function useErrorRecovery() {
  const [error, setError] = React.useState<Error | null>(null);
  const [isRecovering, setIsRecovering] = React.useState(false);
  const [retryCount, setRetryCount] = React.useState(0);

  const recover = React.useCallback(() => {
    setError(null);
    setIsRecovering(false);
    setRetryCount(0);
  }, []);

  const retry = React.useCallback(async (fn: () => Promise<any>) => {
    setIsRecovering(true);
    setRetryCount(prev => prev + 1);

    try {
      const result = await fn();
      recover();
      return result;
    } catch (err) {
      setError(err as Error);
      setIsRecovering(false);
      throw err;
    }
  }, [recover]);

  return {
    error,
    isRecovering,
    retryCount,
    retry,
    recover,
    setError,
  };
}

export default ErrorBoundary;