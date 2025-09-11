/**
 * Terminal Status Debug Component
 * 
 * Displays real-time status of Terminal 2 verification services
 * and allows manual testing of terminal communication
 * 
 * @fileoverview Debug component for terminal verification
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  Paper,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
  Badge
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Analytics as AnalyticsIcon,
  NetworkCheck as NetworkIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Info as InfoIcon
} from '@mui/icons-material';

import useTerminalServices, { 
  useTerminalConnection, 
  usePerformanceAlerts 
} from '../../hooks/useTerminalServices';

// ================================
// MAIN COMPONENT
// ================================

const TerminalStatus: React.FC = () => {
  const {
    status,
    runVerification,
    sendMessage,
    getPerformanceSummary,
    startMonitoring,
    stopMonitoring,
    isHealthy,
    refresh
  } = useTerminalServices();

  const { isConnected: terminal1Connected } = useTerminalConnection('terminal1');
  const { isConnected: terminal3Connected } = useTerminalConnection('terminal3');
  const { alerts, criticalCount } = usePerformanceAlerts();

  const [isRunningVerification, setIsRunningVerification] = useState(false);
  const [lastVerificationResults, setLastVerificationResults] = useState<any[]>([]);

  // ================================
  // EVENT HANDLERS
  // ================================

  const handleRunVerification = async () => {
    setIsRunningVerification(true);
    try {
      const results = await runVerification();
      setLastVerificationResults(results);
      console.log('📊 Verification completed:', results);
    } catch (error) {
      console.error('❌ Verification failed:', error);
    } finally {
      setIsRunningVerification(false);
    }
  };

  const handleSendTestMessage = async () => {
    try {
      const success = await sendMessage('terminal1', {
        to: 'terminal1',
        type: 'test_ping',
        payload: { 
          message: 'Hello from Terminal 2!', 
          timestamp: new Date().toISOString() 
        },
        priority: 'normal'
      });
      
      if (success) {
        console.log('✅ Test message sent successfully');
      } else {
        console.warn('⚠️ Test message failed to send');
      }
    } catch (error) {
      console.error('❌ Test message error:', error);
    }
  };

  // ================================
  // RENDER HELPERS
  // ================================

  const renderConnectionStatus = (terminalId: string, isConnected: boolean) => (
    <Chip
      label={`Terminal ${terminalId.slice(-1)}`}
      color={isConnected ? 'success' : 'error'}
      variant="outlined"
      size="small"
      icon={isConnected ? <SuccessIcon /> : <ErrorIcon />}
    />
  );

  const renderServiceStatus = (service: string, isActive: boolean, details?: any) => (
    <Box display="flex" alignItems="center" gap={1} mb={1}>
      <Chip
        label={service}
        color={isActive ? 'success' : 'warning'}
        variant="filled"
        size="small"
      />
      {details && (
        <Typography variant="caption" color="text.secondary">
          {typeof details === 'object' ? JSON.stringify(details).slice(0, 50) + '...' : details}
        </Typography>
      )}
    </Box>
  );

  const renderVerificationResult = (result: any, index: number) => (
    <Paper key={index} elevation={1} sx={{ p: 1, mb: 1 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="body2" fontWeight="medium">
          {result.service}
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <Chip
            label={result.status}
            color={
              result.status === 'healthy' ? 'success' :
              result.status === 'degraded' ? 'warning' : 'error'
            }
            size="small"
          />
          <Typography variant="caption">
            {result.latency}ms
          </Typography>
        </Box>
      </Box>
      {result.details?.errorMessage && (
        <Typography variant="caption" color="error.main" sx={{ mt: 0.5 }}>
          {result.details.errorMessage}
        </Typography>
      )}
    </Paper>
  );

  // ================================
  // MAIN RENDER
  // ================================

  return (
    <Box p={2}>
      <Typography variant="h4" gutterBottom>
        Terminal 2 Status Dashboard
      </Typography>

      {/* Overall Health Status */}
      <Alert 
        severity={isHealthy ? 'success' : 'warning'} 
        sx={{ mb: 2 }}
        action={
          <IconButton onClick={refresh} size="small">
            <RefreshIcon />
          </IconButton>
        }
      >
        <Typography variant="subtitle1">
          {isHealthy ? 'All systems operational' : 'Some systems need attention'}
        </Typography>
      </Alert>

      <Grid container spacing={2}>
        
        {/* Connection Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <NetworkIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Terminal Connections
              </Typography>
              
              <Box display="flex" gap={1} mb={2}>
                {renderConnectionStatus('terminal1', terminal1Connected)}
                {renderConnectionStatus('terminal3', terminal3Connected)}
                <Chip
                  label="Debugger"
                  color="info"
                  variant="outlined"
                  size="small"
                  icon={<InfoIcon />}
                />
              </Box>

              <Typography variant="body2" color="text.secondary">
                Messages: {status.sync.messageStats.sent} sent, {status.sync.messageStats.received} received
                {status.sync.messageStats.queued > 0 && (
                  <>, {status.sync.messageStats.queued} queued</>
                )}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Service Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Monitoring Services
              </Typography>
              
              {renderServiceStatus('Verification', status.verification.isMonitoring)}
              {renderServiceStatus('Performance', status.performance.isMonitoring, 
                status.performance.score ? `Score: ${status.performance.score}` : undefined)}
              
              <Box mt={2}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={status.verification.isMonitoring ? stopMonitoring : startMonitoring}
                  startIcon={status.verification.isMonitoring ? <StopIcon /> : <StartIcon />}
                  sx={{ mr: 1 }}
                >
                  {status.verification.isMonitoring ? 'Stop' : 'Start'} Monitoring
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleSendTestMessage}
                  disabled={!terminal1Connected}
                >
                  Send Test Message
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Alerts */}
        {(alerts.length > 0 || criticalCount > 0) && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Badge badgeContent={criticalCount} color="error">
                    <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  </Badge>
                  Performance Alerts ({alerts.length})
                </Typography>
                
                <Box maxHeight={200} overflow="auto">
                  {alerts.slice(0, 5).map((alert, index) => (
                    <Alert 
                      key={index} 
                      severity={alert.severity === 'critical' ? 'error' : alert.severity}
                      sx={{ mb: 1 }}
                    >
                      <Typography variant="body2">
                        {alert.message}
                      </Typography>
                      {alert.suggestion && (
                        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                          💡 {alert.suggestion}
                        </Typography>
                      )}
                    </Alert>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Verification Results */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  <SpeedIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Service Verification
                </Typography>
                <Tooltip title="Run verification check">
                  <IconButton 
                    onClick={handleRunVerification}
                    disabled={isRunningVerification}
                    size="small"
                  >
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>

              {isRunningVerification && (
                <Box mb={2}>
                  <LinearProgress />
                  <Typography variant="caption" color="text.secondary">
                    Running verification checks...
                  </Typography>
                </Box>
              )}

              {lastVerificationResults.length > 0 ? (
                <Box maxHeight={300} overflow="auto">
                  {lastVerificationResults.map((result, index) => 
                    renderVerificationResult(result, index)
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No verification results yet. Click refresh to run verification.
                </Typography>
              )}

              <Button
                variant="contained"
                size="small"
                onClick={handleRunVerification}
                disabled={isRunningVerification}
                startIcon={<RefreshIcon />}
                fullWidth
                sx={{ mt: 2 }}
              >
                {isRunningVerification ? 'Running...' : 'Run Full Verification'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Summary */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Summary
              </Typography>
              
              {status.performance.summary ? (
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {status.performance.summary.score}
                      </Typography>
                      <Typography variant="caption">Performance Score</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="info.main">
                        {Math.round(status.performance.summary.metrics.largestContentfulPaint)}ms
                      </Typography>
                      <Typography variant="caption">LCP</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {Math.round(status.performance.summary.metrics.firstContentfulPaint)}ms
                      </Typography>
                      <Typography variant="caption">FCP</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {status.performance.summary.systemHealth.memory_usage}MB
                      </Typography>
                      <Typography variant="caption">Memory</Typography>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Performance monitoring not active
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TerminalStatus;