/**
 * withErrorBoundary HOC
 *
 * Wraps components with error boundary functionality to catch and handle
 * JavaScript errors gracefully in the component tree.
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AtomicBox, AtomicText, AtomicButton } from '../atoms';

export interface WithErrorBoundaryProps {
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  fallback?: React.ComponentType<ErrorBoundaryFallbackProps>;
  resetOnPropsChange?: boolean;
  resetKeys?: Array<string | number | boolean | null | undefined>;
}

export interface ErrorBoundaryFallbackProps {
  error: Error;
  resetError: () => void;
  componentStack: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

// Default fallback component
const DefaultErrorFallback: React.FC<ErrorBoundaryFallbackProps> = ({
  error,
  resetError,
  componentStack
}) => (
  <AtomicBox
    p={6}
    border="1px solid"
    borderRadius="lg"
    bg="rgba(239, 68, 68, 0.1)"
    borderColor="error.main"
    textAlign="center"
  >
    <AtomicText variant="h5" color="error" weight="bold">
      Something went wrong
    </AtomicText>

    <AtomicText variant="body1" color="text.secondary" mt={2}>
      An unexpected error occurred. Please try again.
    </AtomicText>

    {process.env.NODE_ENV === 'development' && (
      <AtomicBox mt={3} p={3} bg="rgba(0,0,0,0.05)" borderRadius="md">
        <AtomicText variant="sm" color="error" weight="medium">
          Error: {error.message}
        </AtomicText>
        {componentStack && (
          <AtomicText variant="xs" color="text.disabled" mt={1}>
            Component Stack: {componentStack}
          </AtomicText>
        )}
      </AtomicBox>
    )}

    <AtomicButton
      variant="outlined"
      color="error"
      onClick={resetError}
      mt={3}
    >
      Try Again
    </AtomicButton>
  </AtomicBox>
);

class ErrorBoundary extends Component<
  {
    children: ReactNode;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
    fallback?: React.ComponentType<ErrorBoundaryFallbackProps>;
    resetOnPropsChange?: boolean;
    resetKeys?: Array<string | number | boolean | null | undefined>;
  },
  ErrorBoundaryState
> {
  private prevResetKeys: Array<string | number | boolean | null | undefined>;

  constructor(props: any) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };

    this.prevResetKeys = props.resetKeys || [];
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      errorInfo
    });

    // Call custom error handler
    this.props.onError?.(error, errorInfo);

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error Boundary caught an error:', error);
      console.error('Component Stack:', errorInfo.componentStack);
    }
  }

  componentDidUpdate(prevProps: any) {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    // Reset error state if resetKeys changed
    if (hasError && resetKeys && resetKeys !== this.prevResetKeys) {
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== this.prevResetKeys[index]
      );

      if (hasResetKeyChanged) {
        this.resetError();
      }
    }

    // Reset error state if any props changed
    if (hasError && resetOnPropsChange && prevProps !== this.props) {
      this.resetError();
    }

    this.prevResetKeys = resetKeys || [];
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback: FallbackComponent = DefaultErrorFallback } = this.props;

    if (hasError && error) {
      return (
        <FallbackComponent
          error={error}
          resetError={this.resetError}
          componentStack={errorInfo?.componentStack || ''}
        />
      );
    }

    return children;
  }
}

/**
 * HOC that wraps a component with error boundary functionality
 *
 * @param WrappedComponent - Component to wrap with error boundary
 * @param options - Error boundary configuration options
 * @returns Enhanced component with error boundary
 *
 * @example
 * const SafeComponent = withErrorBoundary(MyComponent, {
 *   onError: (error, errorInfo) => {
 *     console.error('Component error:', error);
 *     // Send to error tracking service
 *   },
 *   resetOnPropsChange: true
 * });
 */
const withErrorBoundary = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: WithErrorBoundaryProps = {}
) => {
  const ComponentWithErrorBoundary = React.forwardRef<any, P>((props, ref) => {
    return (
      <ErrorBoundary {...options}>
        <WrappedComponent {...props} ref={ref} />
      </ErrorBoundary>
    );
  });

  ComponentWithErrorBoundary.displayName = `withErrorBoundary(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return ComponentWithErrorBoundary;
};

export type { WithErrorBoundaryProps, ErrorBoundaryFallbackProps };
export default withErrorBoundary;