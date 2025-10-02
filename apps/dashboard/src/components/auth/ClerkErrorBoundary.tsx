/**
 * Clerk Error Boundary Component (2025)
 * Handles errors in Clerk authentication components
 */

import React from 'react';
import { Alert, Box, Button, Text, Title } from '@mantine/core';
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
          p="md"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            maxWidth: 500,
            margin: '0 auto',
            marginTop: '1rem'
          }}
        >
          <Alert
            color="red"
            icon={<IconAlertCircle size={16} />}
            title="Authentication Error"
            style={{ width: '100%', marginBottom: '1rem' }}
          >
            <Text size="sm" mb="md">
              {this.state.error?.message || 'An error occurred with the authentication system.'}
            </Text>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <Box
                component="details"
                style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  fontFamily: 'monospace'
                }}
              >
                <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>
                  Error Details (Development)
                </summary>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                  {this.state.error?.stack}
                  {'\n\nComponent Stack:'}
                  {this.state.errorInfo.componentStack}
                </pre>
              </Box>
            )}
          </Alert>

          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={this.handleRetry}
            style={{ marginTop: '1rem' }}
          >
            Try Again
          </Button>

          <Text
            size="sm"
            c="dimmed"
            style={{ marginTop: '1rem', textAlign: 'center' }}
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