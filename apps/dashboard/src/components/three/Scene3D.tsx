import React, { useEffect, useRef, Suspense, Component } from 'react';
import {
  Box, Button, Text, Paper, Stack, SimpleGrid, Container, ActionIcon, Avatar, Card,
  Group, List, Divider, TextInput, Select, Badge, Alert, Loader,
  Progress, Modal, Drawer, Tabs, Menu, Tooltip, Checkbox, Radio,
  Switch, Slider, Rating, Skeleton, Table, useMantineTheme
} from '@mantine/core';
import { useThree } from './useThree';

// Helper function for color transparency (replaces MUI alpha)
const alpha = (color: string, opacity: number) => {
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
};

// Error Boundary for 3D Scene
class Scene3DErrorBoundary extends Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    console.warn('Scene3D Error:', error.message);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.warn('Scene3D Component Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <Box
          style={{
            width: '100%',
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)'
          }}
        >
          <Alert color="yellow" variant="light">
            3D Scene Error - Using Fallback
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

interface Scene3DProps {
  children?: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
  fallback?: React.ReactNode;
  onError?: (error: Error) => void;
}

export const Scene3D: React.FunctionComponent<Scene3DProps> = ({
  children,
  style,
  className,
  fallback = <Loader />,
  onError
}) => {
  // Test environment detection
  const isTestEnvironment = process.env.NODE_ENV === 'test' || typeof window === 'undefined';

  // Safe hook usage with fallbacks
  const { renderer, isWebGLAvailable, cleanup } = (() => {
    try {
      if (!isTestEnvironment) {
        return useThree();
      }
    } catch (error) {
      console.warn('useThree hook failed in Scene3D:', error);
      onError?.(error as Error);
    }

    // Fallback for test environment
    return {
      renderer: null,
      isWebGLAvailable: false,
      cleanup: () => {},
      scene: null,
      camera: null,
      performanceLevel: 'low' as const,
      addObject: () => {},
      removeObject: () => {}
    };
  })();

  const containerRef = useRef<HTMLDivElement>(null);
  const mountedRef = useRef(false);

  useEffect(() => {
    if (!isWebGLAvailable || !renderer || !containerRef.current || isTestEnvironment) return;

    try {
      // Mount renderer
      if (!mountedRef.current) {
        containerRef.current.appendChild(renderer.domElement);
        mountedRef.current = true;
      }

      return () => {
        // Cleanup on unmount
        if (mountedRef.current && containerRef.current && renderer.domElement.parentNode === containerRef.current) {
          containerRef.current.removeChild(renderer.domElement);
          mountedRef.current = false;
        }
        cleanup();
      };
    } catch (error) {
      console.error('Scene3D mounting error:', error);
      onError?.(error as Error);
    }
  }, [renderer, isWebGLAvailable, cleanup, onError, isTestEnvironment]);

  if (!isWebGLAvailable || isTestEnvironment) {
    return (
      <Scene3DErrorBoundary fallback={fallback}>
        <Box
          style={{
            width: '100%',
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)'
          }}
        >
          {fallback}
        </Box>
      </Scene3DErrorBoundary>
    );
  }

  return (
    <Scene3DErrorBoundary fallback={fallback}>
      <Box
        ref={containerRef}
        className={className}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100vh',
          zIndex: -1,
          pointerEvents: 'none',
          ...style
        }}
      >
        <Suspense fallback={fallback}>
          {children}
        </Suspense>
      </Box>
    </Scene3DErrorBoundary>
  );
};export default Scene3D;
