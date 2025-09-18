/**
 * Dashboard Health Check Component
 * Tests all critical dashboard functionality
 */

import React, { useEffect, useState } from 'react';
import { Box, Paper, Typography, Chip, List, ListItem, ListItemIcon, ListItemText, CircularProgress, Button } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAuth } from '../../hooks/useAuth';
import { useRealtimeStatus, useDashboardUpdates } from '../../hooks/useRealtime';
import { tokenRefreshManager } from '../../utils/tokenRefreshManager';
import { configHealthCheck } from '../../utils/configHealthCheck';
import apiClient from '../../services/api';

interface HealthCheckItem {
  name: string;
  status: 'success' | 'warning' | 'error' | 'loading';
  message: string;
  details?: any;
}

export const DashboardHealthCheck: React.FC = () => {
  const [checks, setChecks] = useState<HealthCheckItem[]>([]);
  const [isChecking, setIsChecking] = useState(false);
  const { isAuthenticated, user, token, refreshUserToken } = useAuth();
  const { connectionStatus, isConnected } = useRealtimeStatus();
  const { lastUpdate } = useDashboardUpdates();

  const runHealthChecks = async () => {
    setIsChecking(true);
    const newChecks: HealthCheckItem[] = [];

    // 1. Auth Check
    newChecks.push({
      name: 'Authentication',
      status: isAuthenticated ? 'success' : 'error',
      message: isAuthenticated
        ? `Authenticated as ${user?.email || 'Unknown'}`
        : 'Not authenticated',
      details: {
        userId: user?.id,
        role: user?.role,
        hasToken: !!token,
      },
    });

    // 2. Token Refresh Manager Check
    const tokenStatus = tokenRefreshManager.getStatus();
    newChecks.push({
      name: 'Token Refresh Manager',
      status: tokenStatus.hasToken ? 'success' : 'warning',
      message: tokenStatus.isRefreshing
        ? 'Currently refreshing token'
        : tokenStatus.needsRefresh
        ? 'Token needs refresh'
        : 'Token refresh scheduled',
      details: {
        ...tokenStatus,
        timeUntilExpiry: `${Math.floor(tokenStatus.timeUntilExpiry / 1000)} seconds`,
      },
    });

    // 3. Pusher/Real-time Connection Check
    newChecks.push({
      name: 'Real-time Connection',
      status: isConnected ? 'success' : 'error',
      message: `Connection status: ${connectionStatus}`,
      details: {
        isConnected,
        connectionStatus,
        lastUpdate: lastUpdate ? JSON.stringify(lastUpdate).slice(0, 100) : 'No updates yet',
      },
    });

    // 4. API Connectivity Check
    try {
      const response = await apiClient.health();
      newChecks.push({
        name: 'API Connectivity',
        status: 'success',
        message: 'API is reachable',
        details: response,
      });
    } catch (error) {
      newChecks.push({
        name: 'API Connectivity',
        status: 'error',
        message: 'API is not reachable',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
      });
    }

    // 5. Configuration Health Check
    try {
      const configHealth = await configHealthCheck.runHealthCheck();
      newChecks.push({
        name: 'Configuration',
        status: configHealth.overall as 'success' | 'warning' | 'error',
        message: `${Object.keys(configHealth.checks).filter(k => configHealth.checks[k as keyof typeof configHealth.checks].status === 'healthy').length} / ${Object.keys(configHealth.checks).length} checks passed`,
        details: configHealth,
      });
    } catch (error) {
      newChecks.push({
        name: 'Configuration',
        status: 'error',
        message: 'Failed to check configuration',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
      });
    }

    // 6. Environment Variables Check
    const envVars = {
      API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
      WS_URL: import.meta.env.VITE_WS_URL,
      PUSHER_KEY: import.meta.env.VITE_PUSHER_KEY,
      PUSHER_CLUSTER: import.meta.env.VITE_PUSHER_CLUSTER,
    };

    const missingEnvVars = Object.entries(envVars).filter(([_, value]) => !value);
    newChecks.push({
      name: 'Environment Variables',
      status: missingEnvVars.length === 0 ? 'success' : 'warning',
      message:
        missingEnvVars.length === 0
          ? 'All environment variables configured'
          : `${missingEnvVars.length} missing environment variables`,
      details: {
        configured: Object.keys(envVars).filter(key => envVars[key as keyof typeof envVars]),
        missing: missingEnvVars.map(([key]) => key),
      },
    });

    // 7. 3D Rendering Check
    const hasWebGL = (() => {
      try {
        const canvas = document.createElement('canvas');
        return !!(
          window.WebGLRenderingContext &&
          (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
        );
      } catch (e) {
        return false;
      }
    })();

    newChecks.push({
      name: '3D Rendering Support',
      status: hasWebGL ? 'success' : 'warning',
      message: hasWebGL ? 'WebGL supported' : 'WebGL not supported (using 2D fallback)',
      details: { hasWebGL },
    });

    // 8. Performance Check
    const memory = (performance as any).memory;
    if (memory) {
      const usedMemoryMB = memory.usedJSHeapSize / 1024 / 1024;
      newChecks.push({
        name: 'Memory Usage',
        status: usedMemoryMB < 100 ? 'success' : usedMemoryMB < 200 ? 'warning' : 'error',
        message: `Using ${usedMemoryMB.toFixed(2)} MB`,
        details: {
          used: `${usedMemoryMB.toFixed(2)} MB`,
          limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`,
        },
      });
    }

    setChecks(newChecks);
    setIsChecking(false);
  };

  useEffect(() => {
    runHealthChecks();
  }, [isAuthenticated, isConnected]);

  const testTokenRefresh = async () => {
    try {
      await tokenRefreshManager.forceRefresh();
      alert('Token refreshed successfully!');
      runHealthChecks();
    } catch (error) {
      alert('Token refresh failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <CircularProgress size={20} />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">Dashboard Health Check</Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={runHealthChecks}
              disabled={isChecking}
              sx={{ mr: 2 }}
            >
              Re-run Checks
            </Button>
            <Button variant="contained" onClick={testTokenRefresh}>
              Test Token Refresh
            </Button>
          </Box>
        </Box>

        <List>
          {checks.map((check, index) => (
            <ListItem key={index}>
              <ListItemIcon>{getStatusIcon(check.status)}</ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1">{check.name}</Typography>
                    <Chip
                      label={check.status}
                      size="small"
                      color={
                        check.status === 'success'
                          ? 'success'
                          : check.status === 'warning'
                          ? 'warning'
                          : 'error'
                      }
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      {check.message}
                    </Typography>
                    {check.details && (
                      <Typography
                        variant="caption"
                        component="pre"
                        sx={{
                          mt: 1,
                          p: 1,
                          backgroundColor: 'grey.100',
                          borderRadius: 1,
                          overflow: 'auto',
                          maxHeight: 200,
                          fontFamily: 'monospace',
                        }}
                      >
                        {JSON.stringify(check.details, null, 2)}
                      </Typography>
                    )}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>

        {checks.length === 0 && !isChecking && (
          <Typography variant="body1" color="textSecondary" align="center">
            Click "Re-run Checks" to start health check
          </Typography>
        )}

        {isChecking && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        )}
      </Paper>
    </Box>
  );
};