/**
 * ThreeJSErrorBoundary Component
 *
 * Error boundary specifically for Three.js/React Three Fiber components
 * Catches and handles Three.js related errors gracefully without crashing the app
 * Also handles WebGL context loss/restoration events
 */
import React, { Component, ReactNode, Suspense } from 'react';
import { Alert, Loader, Box, Text, Button, Group } from '@mantine/core';
import { IconAlertCircle, IconRefresh } from '@tabler/icons-react';
import { webglContextManager } from '@/utils/webglContextManager';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  contextId?: string; // Unique ID for WebGL context tracking
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
  contextLost: boolean;
}

/**
 * Error boundary for Three.js components
 * Catches errors from @react-three/fiber, @react-three/drei, and three.js
 */
export class ThreeJSErrorBoundary extends Component<Props, State> {
  private canvasRef: HTMLElement | null = null;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, contextLost: false };
  }

  componentDidMount() {
    // Add WebGL context event listeners
    if (typeof window !== 'undefined') {
      window.addEventListener('webglcontextlost', this.handleContextLost, false);
      window.addEventListener('webglcontextrestored', this.handleContextRestored, false);
    }

    // Log context manager stats
    const stats = webglContextManager.getStats();
    console.log('[ThreeJS Error Boundary] WebGL contexts:', stats);
  }

  componentWillUnmount() {
    // Remove event listeners
    if (typeof window !== 'undefined') {
      window.removeEventListener('webglcontextlost', this.handleContextLost);
      window.removeEventListener('webglcontextrestored', this.handleContextRestored);
    }

    // Unregister from context manager if contextId provided
    if (this.props.contextId) {
      webglContextManager.unregister(this.props.contextId);
    }
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    console.warn('[ThreeJS Error Boundary] Caught error:', error.message);
    return { hasError: true, error, contextLost: false };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details
    console.error('[ThreeJS Error Boundary] Error details:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    });

    // Call optional error handler
    this.props.onError?.(error, errorInfo);

    // Update state with error info
    this.setState({ errorInfo });
  }

  handleContextLost = (event: Event) => {
    console.warn('[ThreeJS Error Boundary] WebGL context lost, attempting recovery...');
    event.preventDefault(); // Prevent default loss behavior
    this.setState({ contextLost: true });

    // Log context manager stats
    const stats = webglContextManager.getStats();
    console.warn('[ThreeJS Error Boundary] Active contexts at loss:', stats);
  };

  handleContextRestored = () => {
    console.log('[ThreeJS Error Boundary] WebGL context restored');
    this.setState({ contextLost: false });

    // Log context manager stats
    const stats = webglContextManager.getStats();
    console.log('[ThreeJS Error Boundary] Active contexts after restore:', stats);
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      contextLost: false
    });
  };

  render() {
    // Show context lost warning (recoverable)
    if (this.state.contextLost) {
      return (
        <Box
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
            minHeight: '200px'
          }}
        >
          <Alert
            icon={<IconAlertCircle size={24} />}
            title="WebGL Context Recovering"
            color="blue"
            variant="light"
            style={{ maxWidth: '500px' }}
          >
            <Text size="sm">
              The WebGL context was lost but is being restored automatically.
              Too many 3D components may be rendering simultaneously.
            </Text>
          </Alert>
        </Box>
      );
    }

    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <Box
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
            minHeight: '200px'
          }}
        >
          <Alert
            icon={<IconAlertCircle size={24} />}
            title="3D Visualization Error"
            color="yellow"
            variant="light"
            style={{ maxWidth: '500px' }}
          >
            <Text size="sm" mb="md">
              There was an issue loading the 3D visualization. This may be due to:
            </Text>
            <ul style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>
              <li>Graphics driver compatibility</li>
              <li>WebGL context limitations (too many 3D components active)</li>
              <li>Browser rendering issues</li>
            </ul>
            <Group gap="sm">
              <Button
                size="sm"
                variant="light"
                leftSection={<IconRefresh size={16} />}
                onClick={this.handleReset}
              >
                Try Again
              </Button>
            </Group>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Box mt="md">
                <Text size="xs" c="dimmed" fw={600}>
                  Error: {this.state.error.message}
                </Text>
              </Box>
            )}
          </Alert>
        </Box>
      );
    }

    // Wrap children in Suspense to handle lazy-loaded Three.js components
    return (
      <Suspense
        fallback={
          <Box
            style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '200px'
            }}
          >
            <Loader size="lg" />
          </Box>
        }
      >
        {this.props.children}
      </Suspense>
    );
  }
}

/**
 * HOC to wrap any component with ThreeJS error boundary
 */
export function withThreeJSErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function ThreeJSBoundaryWrapper(props: P) {
    return (
      <ThreeJSErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ThreeJSErrorBoundary>
    );
  };
}

export default ThreeJSErrorBoundary;
