/**
 * Clerk Error Boundary Component (2025 - Migrated to Mantine v8)
 * Handles errors in Clerk authentication components
 */

import React from 'react';
import { Alert, Box, Button, Text, Code } from '@mantine/core';
import { IconRefresh, IconAlertCircle } from '@tabler/icons-react';

interface ClerkErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ClerkErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export class ClerkErrorBoundary extends React.Component<
  ClerkErrorBoundaryProps,
  ClerkErrorBoundaryState
> {
  constructor(props: ClerkErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ClerkErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Log error for monitoring
    console.error('Clerk Error Boundary caught an error:', error, errorInfo);

    // Call optional error handler
    this.props.onError?.(error, errorInfo);

    // Report to monitoring service (if available)
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: `Clerk Error: ${error.message}`,
        fatal: false
      });
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return (
          <FallbackComponent
            error={this.state.error!}
            retry={this.handleRetry}
          />
        );
      }

      // Default fallback UI
      return (
        <Box
          p="xl"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            maxWidth: 500,
            margin: '2rem auto',
          }}
        >
          <Alert
            icon={<IconAlertCircle size={20} />}
            title="Authentication Error"
            color="red"
            style={{ width: '100%', marginBottom: '1rem' }}
          >
            <Text size="sm" mb="sm">
              {this.state.error?.message || 'An error occurred with the authentication system.'}
            </Text>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <Box
                component="details"
                mt="sm"
                p="sm"
                style={{
                  backgroundColor: 'var(--mantine-color-gray-1)',
                  borderRadius: 'var(--mantine-radius-sm)',
                  fontSize: '0.75rem',
                  fontFamily: 'monospace',
                }}
              >
                <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>
                  Error Details (Development)
                </summary>
                <Code block style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                  {this.state.error?.stack}
                  {'\n\nComponent Stack:'}
                  {this.state.errorInfo.componentStack}
                </Code>
              </Box>
            )}
          </Alert>

          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={this.handleRetry}
            mt="md"
            color="blue"
          >
            Try Again
          </Button>

          <Text
            size="sm"
            c="dimmed"
            mt="md"
            ta="center"
          >
            If this problem persists, please refresh the page or contact support.
          </Text>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Hook for functional components to access error boundary
export const useClerkErrorHandler = () => {
  return React.useCallback((error: Error) => {
    console.error('Clerk error:', error);

    // You could dispatch to a global error store here
    // store.dispatch(addError({ message: error.message, type: 'clerk' }));
  }, []);
};

export default ClerkErrorBoundary;
