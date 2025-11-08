/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the component tree,
 * logs errors, and displays a fallback UI
 */

import React, { Component, type ErrorInfo, type ReactNode } from 'react';
import {
  Box,
  Container,
  Text,
  Title,
  Button,
  Paper,
  Alert,
  Collapse,
  Group,
  useMantineTheme,
  ScrollArea,
  Center,
} from '@mantine/core';
import {
  IconAlertCircle,
  IconRefresh,
  IconChevronDown,
  IconChevronUp,
  IconHome,
  IconCopy,
  IconCheck,
} from '@tabler/icons-react';

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

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
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

  override componentWillUnmount() {
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

  override render() {
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
  errorInfo: _errorInfo,
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
  // Always call the hook - React Hooks must be called unconditionally
  const mantineTheme = useMantineTheme();

  // Fallback theme values in case Mantine theme is incomplete
  const theme = mantineTheme || {
    colors: {
      red: ['#fff5f5', '#fed7d7', '#feb2b2', '#fc8181', '#f56565', '#e53e3e', '#c53030', '#9b2c2c', '#742a2a', '#2d1b1b'],
      gray: ['#f7fafc', '#edf2f7', '#e2e8f0', '#cbd5e0', '#a0aec0', '#718096', '#4a5568', '#2d3748', '#1a202c', '#171923'],
      green: ['#f0fff4', '#c6f6d5', '#9ae6b4', '#68d391', '#48bb78', '#38a169', '#2f855a', '#276749', '#22543d', '#1c4532']
    },
    radius: { sm: 4 }
  };

  // Different layouts based on error level
  if (level === 'page') {
    return (
      <Container size="md" py="xl">
        <Paper
          shadow="md"
          p="xl"
          radius="md"
          style={{
            textAlign: 'center',
            borderTop: `4px solid ${theme.colors.red[6]}`,
          }}
        >
          <Center mb="md">
            <IconAlertCircle
              size={80}
              color={theme.colors.red[6]}
            />
          </Center>

          <Title order={2} mb="md">
            Oops! Something went wrong
          </Title>

          <Text c="dimmed" mb="xl">
            We're sorry, but something unexpected happened. The error has been logged
            and we'll look into it.
          </Text>

          {errorCount >= 3 && (
            <Alert
              icon={<IconAlertCircle size={20} />}
              color="yellow"
              mb="lg"
            >
              Multiple errors detected. The page may be unstable.
            </Alert>
          )}

          <Group justify="center" mb="lg">
            <Button
              leftSection={<IconRefresh size={20} />}
              onClick={onReset}
              disabled={isRecovering}
              variant="filled"
            >
              {isRecovering ? 'Recovering...' : 'Try Again'}
            </Button>

            <Button
              leftSection={<IconHome size={20} />}
              onClick={onGoHome}
              variant="outline"
            >
              Go to Homepage
            </Button>
          </Group>

          {showDetailsProp && (
            <>
              <Button
                size="sm"
                onClick={onToggleDetails}
                rightSection={showDetails ? <IconChevronUp size={18} /> : <IconChevronDown size={18} />}
                variant="subtle"
              >
                {showDetails ? 'Hide' : 'Show'} Technical Details
              </Button>

              <Collapse in={showDetails}>
                <Box mt="lg" style={{ textAlign: 'left' }}>
                  <Alert
                    icon={<IconAlertCircle size={20} />}
                    title="Error Message"
                    color="red"
                    mb="md"
                  >
                    <Text size="sm" style={{ fontFamily: 'monospace' }}>
                      {error.message}
                    </Text>
                  </Alert>

                  {error.stack && (
                    <Paper p="md" withBorder bg="gray.0">
                      <Group justify="space-between" mb="sm">
                        <Text size="sm" fw={500}>
                          Stack Trace
                        </Text>
                        <ActionIcon
                          size="sm"
                          onClick={onCopy}
                          variant="subtle"
                        >
                          {copied ? <IconCheck color="green" size={18} /> : <IconCopy size={18} />}
                        </ActionIcon>
                      </Group>
                      <ScrollArea h={200}>
                        <Text
                          size="xs"
                          component="pre"
                          style={{
                            fontFamily: 'monospace',
                            overflow: 'auto',
                          }}
                        >
                          {error.stack}
                        </Text>
                      </ScrollArea>
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
      p={level === 'section' ? 'lg' : 'md'}
      style={{
        border: `1px solid ${theme.colors.red[6]}`,
        borderRadius: theme.radius.sm,
        backgroundColor: theme.colors.red[0],
      }}
    >
      <Group>
        <IconAlertCircle color={theme.colors.red[6]} size={24} />
        <Box style={{ flex: 1 }}>
          <Text c="red" fw={500}>
            {level === 'section' ? 'Section Error' : 'Component Error'}
          </Text>
          <Text size="sm" c="dimmed">
            {error.message}
          </Text>
        </Box>
        <Button
          size="xs"
          variant="outline"
          onClick={onReset}
          disabled={isRecovering}
        >
          Retry
        </Button>
      </Group>
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