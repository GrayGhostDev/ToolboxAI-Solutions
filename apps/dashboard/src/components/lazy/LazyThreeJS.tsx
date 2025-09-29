import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
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
  message = "Loading 3D environment..."
}: { message?: string }) => (
  <Box
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    minHeight={300}
    gap={2}
    bgcolor="background.paper"
    borderRadius={1}
    border="1px solid"
    borderColor="divider"
  >
    <CircularProgress size={40} />
    <Typography size="sm" color="text.secondary">
      {message}
    </Typography>
  </Box>
);

// Error fallback component
const ThreeErrorFallback = ({ error }: { error?: Error }) => (
  <Box
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    minHeight={300}
    gap={2}
    bgcolor="error.light"
    borderRadius={1}
    p={3}
  >
    <Typography order={6} color="error.main">
      3D Environment Unavailable
    </Typography>
    <Typography size="sm" color="text.secondary" textAlign="center">
      {error?.message || "Unable to load 3D components. Please try refreshing the page."}
    </Typography>
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
  width = "100%",
  height = 400,
  children,
  fallback,
  loadingMessage = "Loading 3D scene..."
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
  loadingMessage = "Initializing 3D environment..."
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