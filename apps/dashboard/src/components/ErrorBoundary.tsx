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
  ActionIcon,
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

// Safe theme hook that doesn't throw when provider is missing
function useSafeMantineTheme() {
  try {
    return { hasMantine: true, theme: useMantineTheme() };
  } catch (error) {
    // MantineProvider is not available
    return { hasMantine: false, theme: null };
  }
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
  const { hasMantine, theme } = useSafeMantineTheme();

  // Fallback UI without Mantine components
  if (!hasMantine) {
    if (level === 'page') {
      return (
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          padding: '3rem 1rem',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            borderTop: '4px solid #fa5252',
            textAlign: 'center'
          }}>
            <div style={{ marginBottom: '1.5rem', color: '#fa5252', fontSize: '4rem' }}>⚠️</div>

            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#212529' }}>
              Oops! Something went wrong
            </h2>

            <p style={{ color: '#868e96', marginBottom: '2rem' }}>
              We're sorry, but something unexpected happened. The error has been logged and we'll look into it.
            </p>

            {errorCount >= 3 && (
              <div style={{
                backgroundColor: '#fff3bf',
                border: '1px solid #fcc419',
                borderRadius: '4px',
                padding: '1rem',
                marginBottom: '1.5rem',
                color: '#f08c00'
              }}>
                ⚠️ Multiple errors detected. The page may be unstable.
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
              <button
                onClick={onReset}
                disabled={isRecovering}
                style={{
                  backgroundColor: '#228be6',
                  color: 'white',
                  border: 'none',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '4px',
                  cursor: isRecovering ? 'not-allowed' : 'pointer',
                  fontSize: '1rem',
                  opacity: isRecovering ? 0.6 : 1
                }}
              >
                {isRecovering ? 'Recovering...' : '🔄 Try Again'}
              </button>

              <button
                onClick={onGoHome}
                style={{
                  backgroundColor: 'transparent',
                  color: '#228be6',
                  border: '1px solid #228be6',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem'
                }}
              >
                🏠 Go to Homepage
              </button>
            </div>

            {showDetailsProp && (
              <>
                <button
                  onClick={onToggleDetails}
                  style={{
                    backgroundColor: 'transparent',
                    color: '#495057',
                    border: 'none',
                    padding: '0.5rem 1rem',
                    cursor: 'pointer',
                    fontSize: '0.875rem'
                  }}
                >
                  {showDetails ? '▲ Hide' : '▼ Show'} Technical Details
                </button>

                {showDetails && (
                  <div style={{ marginTop: '1.5rem', textAlign: 'left' }}>
                    <div style={{
                      backgroundColor: '#ffe3e3',
                      border: '1px solid #fa5252',
                      borderRadius: '4px',
                      padding: '1rem',
                      marginBottom: '1rem'
                    }}>
                      <strong style={{ color: '#c92a2a' }}>Error Message</strong>
                      <pre style={{
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        margin: '0.5rem 0 0 0',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}>
                        {error.message}
                      </pre>
                    </div>

                    {error.stack && (
                      <div style={{
                        backgroundColor: '#f8f9fa',
                        border: '1px solid #dee2e6',
                        borderRadius: '4px',
                        padding: '1rem'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                          <strong>Stack Trace</strong>
                          <button
                            onClick={onCopy}
                            style={{
                              backgroundColor: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '1rem'
                            }}
                          >
                            {copied ? '✅' : '📋'}
                          </button>
                        </div>
                        <div style={{
                          maxHeight: '200px',
                          overflow: 'auto',
                          backgroundColor: 'white',
                          padding: '0.5rem',
                          borderRadius: '4px'
                        }}>
                          <pre style={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            margin: 0,
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                          }}>
                            {error.stack}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      );
    }

    // Inline error without Mantine
    return (
      <div style={{
        border: '1px solid #fa5252',
        borderRadius: '4px',
        backgroundColor: '#fff5f5',
        padding: level === 'section' ? '1.5rem' : '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <span style={{ color: '#fa5252', fontSize: '1.5rem' }}>⚠️</span>
        <div style={{ flex: 1 }}>
          <strong style={{ color: '#fa5252' }}>
            {level === 'section' ? 'Section Error' : 'Component Error'}
          </strong>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#868e96' }}>
            {error.message}
          </p>
        </div>
        <button
          onClick={onReset}
          disabled={isRecovering}
          style={{
            backgroundColor: 'transparent',
            color: '#228be6',
            border: '1px solid #228be6',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            cursor: isRecovering ? 'not-allowed' : 'pointer',
            fontSize: '0.875rem',
            opacity: isRecovering ? 0.6 : 1
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  // Use Mantine components when provider is available
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
