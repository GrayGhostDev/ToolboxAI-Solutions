/**
 * IntegrationHealthMonitor Component
 * Comprehensive monitoring dashboard for all service integrations
 */
import { memo, useEffect, useState, useMemo } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import CircularProgress from '@mui/material/CircularProgress';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Badge from '@mui/material/Badge';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

import {
  CheckCircle as HealthyIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandIcon,
  Database as DatabaseIcon,
  Api as APIIcon,
  Hub as AgentIcon,
  Games as RobloxIcon,
  Stream as RealtimeIcon,
  Speed as PerformanceIcon,
  Timeline as TrendIcon,
  Notifications as AlertIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

import { motion } from 'framer-motion';
import { usePusher } from '@/hooks/usePusher';
import { api } from '@/services/api';

export interface IntegrationHealth {
  healthy: boolean;
  checks: Record<string, any>;
  timestamp: string;
}

export interface HealthOverview {
  status: string;
  health_percentage: number;
  healthy_services: number;
  total_services: number;
  integrations: {
    database_integrations: IntegrationHealth;
    api_integrations: IntegrationHealth;
    realtime_integrations: IntegrationHealth;
    agent_integrations: IntegrationHealth;
    roblox_integrations: IntegrationHealth;
  };
  check_duration_ms: number;
}

export interface IntegrationHealthMonitorProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
  showDetails?: boolean;
  onIntegrationClick?: (integration: string, health: IntegrationHealth) => void;
}

const MotionPaper = motion(Paper);

export const IntegrationHealthMonitor = memo<IntegrationHealthMonitorProps>(({
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
  showDetails = true,
  onIntegrationClick,
}) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedTab, setSelectedTab] = useState(0);
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>('overview');

  // Health data
  const [healthOverview, setHealthOverview] = useState<HealthOverview | null>(null);
  const [detailedHealth, setDetailedHealth] = useState<Record<string, IntegrationHealth>>({});

  // Setup Pusher for real-time updates
  const { subscribe, unsubscribe } = usePusher();

  useEffect(() => {
    const channel = 'system-health';

    const handleHealthUpdate = (data: HealthOverview) => {
      setHealthOverview(data);
      setLastUpdate(new Date());
    };

    const handleIntegrationUpdate = (data: { integration: string; health: IntegrationHealth }) => {
      setDetailedHealth(prev => ({
        ...prev,
        [data.integration]: data.health,
      }));
    };

    subscribe(channel, 'health-overview', handleHealthUpdate);
    subscribe(channel, 'integration-update', handleIntegrationUpdate);

    return () => {
      unsubscribe(channel, 'health-overview', handleHealthUpdate);
      unsubscribe(channel, 'integration-update', handleIntegrationUpdate);
    };
  }, [subscribe, unsubscribe]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const fetchHealthData = async () => {
        try {
          setLoading(true);
          setError(null);

          // Fetch overview
          const overviewResponse = await api.get('/api/v1/health/integrations');
          setHealthOverview(overviewResponse.data);

          // Fetch detailed health for each integration
          const integrationTypes = ['database', 'apis', 'realtime', 'agents', 'roblox'];
          const detailedPromises = integrationTypes.map(async (type) => {
            try {
              const response = await api.get(`/api/v1/health/${type}`);
              return { type, data: response.data };
            } catch (error) {
              console.error(`Failed to fetch ${type} health:`, error);
              return { type, data: null };
            }
          });

          const detailedResults = await Promise.all(detailedPromises);
          const detailedData: Record<string, IntegrationHealth> = {};

          detailedResults.forEach(({ type, data }) => {
            if (data) {
              detailedData[type] = data;
            }
          });

          setDetailedHealth(detailedData);
          setLastUpdate(new Date());
        } catch (err: any) {
          setError(`Failed to fetch health data: ${err.message}`);
        } finally {
          setLoading(false);
        }
      };

      fetchHealthData();
      const interval = setInterval(fetchHealthData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return theme.palette.success.main;
      case 'degraded':
        return theme.palette.warning.main;
      case 'unhealthy':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon fontSize="small" />;
      case 'degraded':
        return <WarningIcon fontSize="small" />;
      case 'unhealthy':
        return <ErrorIcon fontSize="small" />;
      default:
        return <InfoIcon fontSize="small" />;
    }
  };

  const getIntegrationIcon = (integration: string) => {
    switch (integration) {
      case 'database_integrations':
        return <DatabaseIcon />;
      case 'api_integrations':
        return <APIIcon />;
      case 'realtime_integrations':
        return <RealtimeIcon />;
      case 'agent_integrations':
        return <AgentIcon />;
      case 'roblox_integrations':
        return <RobloxIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const getIntegrationName = (integration: string) => {
    switch (integration) {
      case 'database_integrations':
        return 'Database Connections';
      case 'api_integrations':
        return 'External APIs';
      case 'realtime_integrations':
        return 'Real-time Services';
      case 'agent_integrations':
        return 'Agent Orchestration';
      case 'roblox_integrations':
        return 'Roblox Integration';
      default:
        return integration.replace('_', ' ');
    }
  };

  const handleRefresh = async () => {
    if (!loading) {
      setLoading(true);
      try {
        const overviewResponse = await api.get('/api/v1/health/integrations');
        setHealthOverview(overviewResponse.data);
        setLastUpdate(new Date());
      } catch (err: any) {
        setError(`Failed to refresh: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? panel : false);
  };

  const renderIntegrationCard = (integrationKey: string, health: IntegrationHealth) => {
    const name = getIntegrationName(integrationKey);
    const icon = getIntegrationIcon(integrationKey);
    const status = health.healthy ? 'healthy' : 'unhealthy';
    const statusColor = getStatusColor(status);

    return (
      <Card
        key={integrationKey}
        sx={{
          cursor: onIntegrationClick ? 'pointer' : 'default',
          borderLeft: `4px solid ${statusColor}`,
          '&:hover': onIntegrationClick
            ? {
                backgroundColor: alpha(theme.palette.primary.main, 0.05),
              }
            : {},
        }}
        onClick={() => onIntegrationClick?.(integrationKey, health)}
      >
        <CardHeader
          avatar={
            <Box sx={{ color: statusColor }}>
              {icon}
            </Box>
          }
          title={name}
          subheader={`Last checked: ${new Date(health.timestamp).toLocaleTimeString()}`}
          action={
            <Chip
              label={status.toUpperCase()}
              size="small"
              color={health.healthy ? 'success' : 'error'}
              icon={getStatusIcon(status)}
            />
          }
        />
        <CardContent sx={{ pt: 0 }}>
          <Stack spacing={1}>
            {Object.entries(health.checks).map(([checkName, checkResult]) => (
              <Box key={checkName} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  {checkName.replace('_', ' ')}
                </Typography>
                <Chip
                  label={checkResult.healthy ? 'OK' : 'ERROR'}
                  size="small"
                  color={checkResult.healthy ? 'success' : 'error'}
                  variant="outlined"
                />
              </Box>
            ))}
          </Stack>
        </CardContent>
      </Card>
    );
  };

  const renderOverviewStats = () => {
    if (!healthOverview) return null;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack spacing={1} alignItems="center">
                <Typography variant="h4" fontWeight="bold" color={getStatusColor(healthOverview.status)}>
                  {healthOverview.health_percentage.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Overall Health
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={healthOverview.health_percentage}
                  sx={{
                    width: '100%',
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: alpha(getStatusColor(healthOverview.status), 0.2),
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getStatusColor(healthOverview.status),
                    },
                  }}
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack spacing={1} alignItems="center">
                <Typography variant="h4" fontWeight="bold" color="success.main">
                  {healthOverview.healthy_services}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Healthy Services
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  out of {healthOverview.total_services}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack spacing={1} alignItems="center">
                <Typography variant="h4" fontWeight="bold" color="primary.main">
                  {healthOverview.check_duration_ms}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Check Duration (ms)
                </Typography>
                <PerformanceIcon color="primary" />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack spacing={1} alignItems="center">
                <Typography variant="h4" fontWeight="bold">
                  {Object.keys(healthOverview.integrations).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Integration Types
                </Typography>
                <TrendIcon color="primary" />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  return (
    <MotionPaper
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            <Typography variant="h6" fontWeight="bold">
              Integration Health Monitor
            </Typography>
            {healthOverview && (
              <Chip
                label={healthOverview.status.toUpperCase()}
                size="small"
                color={
                  healthOverview.status === 'healthy'
                    ? 'success'
                    : healthOverview.status === 'degraded'
                    ? 'warning'
                    : 'error'
                }
                icon={getStatusIcon(healthOverview.status)}
              />
            )}
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Tooltip title="Last updated">
              <Typography variant="caption" color="text.secondary">
                {lastUpdate.toLocaleTimeString()}
              </Typography>
            </Tooltip>
            <IconButton size="small" onClick={handleRefresh} disabled={loading}>
              {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
            </IconButton>
          </Stack>
        </Stack>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {error && (
          <Alert severity="error" sx={{ m: 2 }}>
            <AlertTitle>Health Check Error</AlertTitle>
            {error}
          </Alert>
        )}

        {/* Overview Stats */}
        {healthOverview && (
          <Accordion
            expanded={expandedAccordion === 'overview'}
            onChange={handleAccordionChange('overview')}
          >
            <AccordionSummary expandIcon={<ExpandIcon />}>
              <Typography variant="h6">Overview Statistics</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {renderOverviewStats()}
            </AccordionDetails>
          </Accordion>
        )}

        {/* Integration Details */}
        {healthOverview && showDetails && (
          <Accordion
            expanded={expandedAccordion === 'integrations'}
            onChange={handleAccordionChange('integrations')}
          >
            <AccordionSummary expandIcon={<ExpandIcon />}>
              <Typography variant="h6">Integration Details</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {Object.entries(healthOverview.integrations).map(([key, health]) => (
                  <Grid item xs={12} lg={6} key={key}>
                    {renderIntegrationCard(key, health)}
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        )}

        {/* Detailed Health by Category */}
        {Object.keys(detailedHealth).length > 0 && (
          <Accordion
            expanded={expandedAccordion === 'detailed'}
            onChange={handleAccordionChange('detailed')}
          >
            <AccordionSummary expandIcon={<ExpandIcon />}>
              <Typography variant="h6">Detailed Health Checks</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Tabs value={selectedTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
                {Object.keys(detailedHealth).map((integration, index) => (
                  <Tab
                    key={integration}
                    label={getIntegrationName(integration)}
                    icon={getIntegrationIcon(integration)}
                  />
                ))}
              </Tabs>

              {Object.entries(detailedHealth).map(([integration, health], index) => (
                <Box
                  key={integration}
                  role="tabpanel"
                  hidden={selectedTab !== index}
                  sx={{ mt: 2 }}
                >
                  {selectedTab === index && (
                    <Card variant="outlined">
                      <CardContent>
                        <pre style={{ fontSize: '0.875rem', overflow: 'auto' }}>
                          {JSON.stringify(health, null, 2)}
                        </pre>
                      </CardContent>
                    </Card>
                  )}
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
        )}
      </Box>
    </MotionPaper>
  );
});

IntegrationHealthMonitor.displayName = 'IntegrationHealthMonitor';
export default IntegrationHealthMonitor;