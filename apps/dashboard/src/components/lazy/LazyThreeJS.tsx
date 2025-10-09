import { Box, Loader, Text, Title } from '@mantine/core';
/**
 * Lazy loading wrapper for Three.js components
 *
 * Reduces initial bundle size by lazy loading Three.js when needed.
 * Shows loading fallback until the component is ready.
 */

import React, { Suspense, lazy } from 'react';

// Lazy load Three.js components - these will be in separate chunks
const Scene3D = lazy(() => import('../three/Scene3D'));
const ThreeProvider = lazy(() => import('../three/ThreeProvider'));

// Loading fallback component
const ThreeLoadingFallback = ({
  message = 'Loading 3D environment...'
}: { message?: string }) => (
  <Box
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 300,
      gap: 16,
      backgroundColor: 'var(--mantine-color-gray-0)',
      borderRadius: 'var(--mantine-radius-md)',
      border: '1px solid var(--mantine-color-gray-3)',
    }}
  >
    <Loader size="lg" />
    <Text size="sm" c="dimmed">
      {message}
    </Text>
  </Box>
);

// Error fallback component
const ThreeErrorFallback = ({ error }: { error?: Error }) => (
  <Box
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 300,
      gap: 16,
      backgroundColor: 'var(--mantine-color-red-0)',
      borderRadius: 'var(--mantine-radius-md)',
      padding: 24,
    }}
  >
    <Title order={6} c="red">
      3D Environment Unavailable
    </Title>
    <Text size="sm" c="dimmed" ta="center">
      {error?.message || 'Unable to load 3D components. Please try refreshing the page.'}
    </Text>
  </Box>
);

// Error boundary for Three.js components
class ThreeErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<{ error?: Error }> },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.warn('Three.js component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || ThreeErrorFallback;
      return <FallbackComponent error={this.state.error} />;
    }

    return this.props.children;
  }
}

// Props interfaces
interface LazyScene3DProps {
  width?: number | string;
  height?: number | string;
  children?: React.ReactNode;
  fallback?: React.ComponentType;
  loadingMessage?: string;
}

interface LazyThreeProviderProps {
  children: React.ReactNode;
  fallback?: React.ComponentType;
  loadingMessage?: string;
}

// Lazy Scene3D component with error handling
export const LazyScene3D = ({
  width = '100%',
  height = 400,
  children,
  fallback,
  loadingMessage = 'Loading 3D scene...'
}: LazyScene3DProps) => {
  return (
    <ThreeErrorBoundary fallback={fallback}>
      <Suspense fallback={<ThreeLoadingFallback message={loadingMessage} />}>
        <Scene3D {...({ width, height } as any)}>
          {children}
        </Scene3D>
      </Suspense>
    </ThreeErrorBoundary>
  );
};

// Lazy ThreeProvider component with error handling
export const LazyThreeProvider = ({
  children,
  fallback,
  loadingMessage = 'Initializing 3D environment...'
}: LazyThreeProviderProps) => {
  return (
    <ThreeErrorBoundary fallback={fallback}>
      <Suspense fallback={<ThreeLoadingFallback message={loadingMessage} />}>
        <ThreeProvider>
          {children}
        </ThreeProvider>
      </Suspense>
    </ThreeErrorBoundary>
  );
};

// Preload Three.js components when user is likely to need them
export const preloadThreeJS = () => {
  // Preload the components without rendering them
  import('../three/Scene3D');
  import('../three/ThreeProvider');
};

// Hook for conditional preloading
export const useThreeJSPreloader = (shouldPreload: boolean = false) => {
  React.useEffect(() => {
    if (shouldPreload) {
      // Preload on user interaction or route change
      const timeoutId = setTimeout(preloadThreeJS, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [shouldPreload]);
};

export default LazyScene3D;