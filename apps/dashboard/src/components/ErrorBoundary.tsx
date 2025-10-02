/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the component tree,
 * logs errors, and displays a fallback UI
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
// Removed Mantine imports - using basic HTML elements instead
import {
  IconAlertCircle,
  IconRefresh,
  IconChevronDown,
  IconChevronUp,
  IconHome,
  IconBug,
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
  // Different layouts based on error level
  if (level === 'page') {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
        <div
          style={{
            textAlign: 'center',
            borderTop: '4px solid #e03131',
            padding: '2rem',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            backgroundColor: 'white',
          }}
        >
          <div style={{ marginBottom: '1rem' }}>
            <IconAlertCircle
              size={80}
              color="#e03131"
            />
          </div>

          <h2 style={{ marginBottom: '1rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
            Oops! Something went wrong
          </h2>

          <p style={{ color: '#666', marginBottom: '2rem' }}>
            We're sorry, but something unexpected happened. The error has been logged
            and we'll look into it.
          </p>

          {errorCount >= 3 && (
            <div
              style={{
                backgroundColor: '#fff3cd',
                border: '1px solid #ffeaa7',
                borderRadius: '4px',
                padding: '1rem',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <IconAlertCircle size={20} color="#856404" />
              <span style={{ color: '#856404' }}>
                Multiple errors detected. The page may be unstable.
              </span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <button
              onClick={onReset}
              disabled={isRecovering}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#e03131',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isRecovering ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <IconRefresh size={20} />
              {isRecovering ? 'Recovering...' : 'Try Again'}
            </button>

            <button
              onClick={onGoHome}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: 'transparent',
                color: '#e03131',
                border: '1px solid #e03131',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <IconHome size={20} />
              Go to Homepage
            </button>
          </div>

          {showDetailsProp && (
            <>
              <button
                onClick={onToggleDetails}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  margin: '0 auto',
                }}
              >
                {showDetails ? 'Hide' : 'Show'} Technical Details
                {showDetails ? <IconChevronUp size={18} /> : <IconChevronDown size={18} />}
              </button>

              {showDetails && (
                <div style={{ marginTop: '1rem', textAlign: 'left' }}>
                  <div
                    style={{
                      backgroundColor: '#ffe0e0',
                      border: '1px solid #e03131',
                      borderRadius: '4px',
                      padding: '1rem',
                      marginBottom: '1rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <IconAlertCircle size={20} color="#e03131" />
                      <strong>Error Message</strong>
                    </div>
                    <div style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      {error.message}
                    </div>
                  </div>

                  {error.stack && (
                    <div
                      style={{
                        padding: '1rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        backgroundColor: '#f8f9fa',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>
                          Stack Trace
                        </span>
                        <button
                          onClick={onCopy}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '0.25rem',
                          }}
                        >
                          {copied ? <IconCheck color="green" size={18} /> : <IconCopy size={18} />}
                        </button>
                      </div>
                      <div
                        style={{
                          height: '200px',
                          overflow: 'auto',
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          backgroundColor: 'white',
                          padding: '0.5rem',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                        }}
                      >
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
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

  // Inline error for sections and components
  return (
    <div
      style={{
        padding: level === 'section' ? '1.5rem' : '1rem',
        border: '1px solid #e03131',
        borderRadius: '4px',
        backgroundColor: '#ffe0e0',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <IconAlertCircle color="#e03131" size={24} />
        <div style={{ flex: 1 }}>
          <div style={{ color: '#e03131', fontWeight: '500' }}>
            {level === 'section' ? 'Section Error' : 'Component Error'}
          </div>
          <div style={{ fontSize: '0.875rem', color: '#666' }}>
            {error.message}
          </div>
        </div>
        <button
          onClick={onReset}
          disabled={isRecovering}
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: 'transparent',
            color: '#e03131',
            border: '1px solid #e03131',
            borderRadius: '4px',
            cursor: isRecovering ? 'not-allowed' : 'pointer',
            fontSize: '0.75rem',
          }}
        >
          Retry
        </button>
      </div>
    </div>
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
