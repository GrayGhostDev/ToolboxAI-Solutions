/**
 * Performance Settings Component
 *
 * UI for controlling performance monitoring feature flags
 * and displaying performance metrics
 */

import React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Grid from '@mui/material/Grid';

import {
  Speed,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Memory,
  Timer,
  TrendingUp,
  Refresh,
  Clear,
} from '@mui/icons-material';
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor';
import { featureFlags, useFeatureFlags } from '@/config/features';

export default function PerformanceSettings() {
  const flags = useFeatureFlags();
  const {
    isMonitoring,
    summary,
    startMonitoring,
    stopMonitoring,
    clearAlerts,
  } = usePerformanceMonitor();

  /**
   * Handle performance monitoring toggle
   */
  const handleMonitoringToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = event.target.checked;
    featureFlags.updateFlags({ enablePerformanceMonitoring: enabled });

    if (enabled) {
      startMonitoring();
    } else {
      stopMonitoring();
    }
  };

  /**
   * Handle monitoring level change
   */
  const handleLevelChange = (event: any) => {
    featureFlags.updateFlags({
      performanceMonitoringLevel: event.target.value,
    });
  };

  /**
   * Get score color based on value
   */
  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'error';
  };

  /**
   * Get severity color
   */
  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' => {
    switch (severity) {
      case 'critical':
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Performance Monitoring
      </Typography>

      {/* Main Settings */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Monitoring Configuration
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={flags.enablePerformanceMonitoring}
                    onChange={handleMonitoringToggle}
                    color="primary"
                  />
                }
                label="Enable Performance Monitoring"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth disabled={!flags.enablePerformanceMonitoring}>
                <InputLabel>Monitoring Level</InputLabel>
                <Select
                  value={flags.performanceMonitoringLevel}
                  onChange={handleLevelChange}
                  label="Monitoring Level"
                >
                  <MenuItem value="off">Off</MenuItem>
                  <MenuItem value="basic">Basic</MenuItem>
                  <MenuItem value="detailed">Detailed</MenuItem>
                  <MenuItem value="verbose">Verbose</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={flags.enableSlowApiWarnings}
                    onChange={(e) =>
                      featureFlags.updateFlags({
                        enableSlowApiWarnings: e.target.checked,
                      })
                    }
                    color="primary"
                  />
                }
                label="Enable Slow API Warnings"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={flags.enableReactProfiler}
                    onChange={(e) =>
                      featureFlags.updateFlags({
                        enableReactProfiler: e.target.checked,
                      })
                    }
                    color="primary"
                  />
                }
                label="Enable React Profiler"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Performance Status */}
      {isMonitoring && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Performance Status</Typography>
              <Chip
                icon={<Speed />}
                label="Monitoring Active"
                color="success"
                size="small"
              />
            </Box>

            {summary ? (
              <>
                {/* Performance Score */}
                <Box mb={3}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Overall Score
                  </Typography>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="h3" color={`${getScoreColor(summary.score)}.main`}>
                      {summary.score}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      / 100
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={summary.score}
                    color={getScoreColor(summary.score) as any}
                    sx={{ mt: 1, height: 8, borderRadius: 1 }}
                  />
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Key Metrics */}
                <Grid container spacing={2}>
                  <Grid item xs={6} md={3}>
                    <Box textAlign="center">
                      <Timer color="action" />
                      <Typography variant="body2" color="text.secondary">
                        FCP
                      </Typography>
                      <Typography variant="h6">
                        {summary.metrics.firstContentfulPaint.toFixed(0)}ms
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={6} md={3}>
                    <Box textAlign="center">
                      <TrendingUp color="action" />
                      <Typography variant="body2" color="text.secondary">
                        LCP
                      </Typography>
                      <Typography variant="h6">
                        {summary.metrics.largestContentfulPaint.toFixed(0)}ms
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={6} md={3}>
                    <Box textAlign="center">
                      <Memory color="action" />
                      <Typography variant="body2" color="text.secondary">
                        Memory
                      </Typography>
                      <Typography variant="h6">
                        {summary.systemHealth.memory_usage}MB
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid item xs={6} md={3}>
                    <Box textAlign="center">
                      <Speed color="action" />
                      <Typography variant="body2" color="text.secondary">
                        CPU
                      </Typography>
                      <Typography variant="h6">{summary.systemHealth.cpu_usage}%</Typography>
                    </Box>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 2 }} />

                {/* Alerts */}
                {summary.alerts.length > 0 && (
                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle1">Active Alerts</Typography>
                      <Button size="small" startIcon={<Clear />} onClick={(e: React.MouseEvent) => clearAlerts}>
                        Clear All
                      </Button>
                    </Box>
                    <Stack spacing={1}>
                      {summary.alerts.slice(-5).map((alert, index) => (
                        <Alert
                          key={index}
                          severity={getSeverityColor(alert.severity)}
                          onClose={() => {}}
                        >
                          <AlertTitle>{alert.message}</AlertTitle>
                          {alert.suggestion && (
                            <Typography variant="body2">{alert.suggestion}</Typography>
                          )}
                        </Alert>
                      ))}
                    </Stack>
                  </Box>
                )}

                {/* Recommendations */}
                {summary.recommendations.length > 0 && (
                  <Box>
                    <Typography variant="subtitle1" gutterBottom>
                      Recommendations
                    </Typography>
                    <Stack spacing={1}>
                      {summary.recommendations.map((rec, index) => (
                        <Box key={index} display="flex" alignItems="center" gap={1}>
                          <CheckCircle color="info" fontSize="small" />
                          <Typography variant="body2">{rec}</Typography>
                        </Box>
                      ))}
                    </Stack>
                  </Box>
                )}
              </>
            ) : (
              <Box textAlign="center" py={3}>
                <Typography color="text.secondary">
                  Collecting performance data...
                </Typography>
                <LinearProgress sx={{ mt: 2 }} />
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Not Monitoring Message */}
      {!isMonitoring && flags.enablePerformanceMonitoring && (
        <Alert severity="info">
          <AlertTitle>Performance Monitoring Ready</AlertTitle>
          Performance monitoring is enabled but not currently active.
          <Button
            size="small"
            startIcon={<Speed />}
            onClick={(e: React.MouseEvent) => startMonitoring}
            sx={{ mt: 1 }}
          >
            Start Monitoring
          </Button>
        </Alert>
      )}

      {/* Disabled Message */}
      {!flags.enablePerformanceMonitoring && (
        <Alert severity="warning">
          <AlertTitle>Performance Monitoring Disabled</AlertTitle>
          Enable performance monitoring to track application metrics and identify optimization
          opportunities.
        </Alert>
      )}
    </Box>
  );
}