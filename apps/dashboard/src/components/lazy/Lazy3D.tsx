import React, { Suspense, lazy } from 'react';
import { Box, Text, Alert, Loader, Skeleton } from '@mantine/core';

// Lazy load 3D components only when needed
const Scene3D = lazy(() => import('../three/Scene3D').then(module => ({ default: module.Scene3D })));
const ThreeProvider = lazy(() => import('../three/ThreeProvider'));

interface Lazy3DProps {
  type: 'scene' | 'icon' | 'character';
  children?: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
  fallbackHeight?: number;
  onError?: (error: Error) => void;
}

// 3D fallback for unsupported browsers
const WebGL3DFallback = ({
  height,
  message = '3D content not available'
}: { height: number; message?: string }) => (
  <Box
    style={{
      height,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
      borderRadius: 8,
    }}
  >
    <Text size="sm" c="dimmed" mb="xs">
      {message}
    </Text>
    <Text size="xs" c="gray.6">
      WebGL not supported or disabled
    </Text>
  </Box>
);

// Enhanced loading skeleton for 3D content
const ThreeDSkeleton = ({ height }: { height: number }) => (
  <Box
    style={{
      height,
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
      borderRadius: 8,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative'
    }}
  >
    <Box style={{ textAlign: 'center', zIndex: 1 }}>
      <Loader size="md" mb="sm" />
      <Text size="sm" c="dimmed">
        Loading 3D content...
      </Text>
    </Box>
    <Skeleton
      width="100%"
      height="100%"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        opacity: 0.1
      }}
    />
  </Box>
);

// WebGL capability detection
const checkWebGLSupport = (): boolean => {
  try {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    return !!context;
  } catch {
    return false;
  }
};

// Error boundary for 3D content
class ThreeDErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; fallback: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('3D content loading error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

export const Lazy3D = ({
  type,
  children,
  style,
  className,
  fallbackHeight = 400,
  onError
}: Lazy3DProps) => {
  const [webglSupported] = React.useState(() => checkWebGLSupport());

  const errorFallback = (
    <Alert
      color="blue"
      title="3D Content Unavailable"
      style={{
        height: fallbackHeight,
        display: 'flex',
        alignItems: 'center',
      }}
    >
      3D content temporarily unavailable. Please check your browser settings.
    </Alert>
  );

  const loadingFallback = <ThreeDSkeleton height={fallbackHeight} />;

  const unsupportedFallback = (
    <WebGL3DFallback
      height={fallbackHeight}
      message="3D content requires WebGL support"
    />
  );

  // Early return for unsupported browsers
  if (!webglSupported) {
    return unsupportedFallback;
  }

  if (type === 'scene') {
    return (
      <ThreeDErrorBoundary fallback={errorFallback}>
        <Suspense fallback={loadingFallback}>
          <ThreeProvider>
            <Scene3D
              style={style}
              className={className}
              onError={onError}
              fallback={loadingFallback}
            >
              {children}
            </Scene3D>
          </ThreeProvider>
        </Suspense>
      </ThreeDErrorBoundary>
    );
  }

  // For other 3D component types (icon, character, etc.)
  return (
    <ThreeDErrorBoundary fallback={errorFallback}>
      <Suspense fallback={loadingFallback}>
        <ThreeProvider>
          <Box
            className={className}
            style={{
              height: fallbackHeight,
              ...style
            }}
          >
            {children}
          </Box>
        </ThreeProvider>
      </Suspense>
    </ThreeDErrorBoundary>
  );
};

export default Lazy3D;