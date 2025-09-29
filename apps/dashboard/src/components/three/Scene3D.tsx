import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import React, { useEffect, useRef, Suspense } from 'react';
import { useThree } from './useThree';

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
  fallback = <CircularProgress />,
  onError
}) => {
  const { renderer, isWebGLAvailable, cleanup } = useThree();
  const containerRef = useRef<HTMLDivElement>(null);
  const mountedRef = useRef(false);

  useEffect(() => {
    if (!isWebGLAvailable || !renderer || !containerRef.current) return;

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
  }, [renderer, isWebGLAvailable, cleanup, onError]);

  if (!isWebGLAvailable) {
    return (
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
    );
  }

  return (
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
  );
};export default Scene3D;
