/**
 * IntegrationHealthMonitor Component
 * Comprehensive monitoring dashboard for all service integrations
 */
import { memo, useEffect, useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Text,
  Title,
  Grid,
  Stack,
  Badge,
  ActionIcon,
  Tooltip,
  Alert,
  Button,
  Collapse,
  Card,
  Divider,
  Progress,
  Loader,
  Group,
  Tabs,
  Accordion,
  useMantineTheme,
  alpha,
} from '@mantine/core';

import {
  IconCircleCheck as HealthyIcon,
  IconX as ErrorIcon,
  IconAlertTriangle as WarningIcon,
  IconRefresh as RefreshIcon,
  IconChevronDown as ExpandIcon,
  IconDatabase as DatabaseIcon,
  IconApi as APIIcon,
  IconNetwork as AgentIcon,
  IconDeviceGamepad as RobloxIcon,
  IconBroadcast as RealtimeIcon,
  IconGauge as PerformanceIcon,
  IconTrendingUp as TrendIcon,
  IconBell as AlertIcon,
  IconInfoCircle as InfoIcon,
} from '@tabler/icons-react';

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
  const theme = useMantineTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedTab, setSelectedTab] = useState(0);
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>('overview');

  // Health data
  const [healthOverview, setHealthOverview] = useState<HealthOverview | null>(null);
  const [detailedHealth, setDetailedHealth] = useState<Record<string, IntegrationHealth>>({});

  // Setup Pusher for real-time updates
  const { service: pusherService, isConnected } = usePusher();

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

    if (!isConnected) return;

    const subscriptions = [
      pusherService.subscribe(channel, (message) => {
        if (message.type === 'health-overview') {
          handleHealthUpdate(message.payload);
        } else if (message.type === 'integration-update') {
          handleIntegrationUpdate(message.payload);
        }
      })
    ];

    return () => {
      subscriptions.forEach(id => pusherService.unsubscribe(id));
    };
  }, [pusherService, isConnected]);

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
        return theme.colors.green[6];
      case 'degraded':
        return theme.colors.yellow[6];
      case 'unhealthy':
        return theme.colors.red[6];
      default:
        return theme.colors.gray[6];
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon size={16} />;
      case 'degraded':
        return <WarningIcon size={16} />;
      case 'unhealthy':
        return <ErrorIcon size={16} />;
      default:
        return <InfoIcon size={16} />;
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
        padding="md"
        withBorder
        style={{
          cursor: onIntegrationClick ? 'pointer' : 'default',
          borderLeft: `4px solid ${statusColor}`,
        }}
        onClick={() => onIntegrationClick?.(integrationKey, health)}
      >
        <Stack gap="md">
          <Group justify="space-between" align="flex-start">
            <Group gap="md">
              <Box style={{ color: statusColor }}>
                {icon}
              </Box>
              <Stack gap="xs">
                <Text fw={500}>{name}</Text>
                <Text size="sm" c="dimmed">
                  Last checked: {new Date(health.timestamp).toLocaleTimeString()}
                </Text>
              </Stack>
            </Group>
            <Badge
              color={health.healthy ? 'green' : 'red'}
              leftSection={getStatusIcon(status)}
            >
              {status.toUpperCase()}
            </Badge>
          </Group>
          <Stack gap="xs">
            {Object.entries(health.checks).map(([checkName, checkResult]) => (
              <Group key={checkName} justify="space-between">
                <Text size="sm" c="dimmed">
                  {checkName.replace('_', ' ')}
                </Text>
                <Badge
                  size="sm"
                  color={checkResult.healthy ? 'green' : 'red'}
                  variant="outline"
                >
                  {checkResult.healthy ? 'OK' : 'ERROR'}
                </Badge>
              </Group>
            ))}
          </Stack>
        </Stack>
      </Card>
    );
  };

  const renderOverviewStats = () => {
    if (!healthOverview) return null;

    return (
      <Grid>
        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md" withBorder>
            <Stack gap="xs" align="center">
              <Text size="xl" fw={700} c={getStatusColor(healthOverview.status)}>
                {healthOverview.health_percentage.toFixed(1)}%
              </Text>
              <Text size="sm" c="dimmed">
                Overall Health
              </Text>
              <Progress
                value={healthOverview.health_percentage}
                color={
                  healthOverview.status === 'healthy'
                    ? 'green'
                    : healthOverview.status === 'degraded'
                    ? 'yellow'
                    : 'red'
                }
                size="sm"
                style={{ width: '100%' }}
              />
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md" withBorder>
            <Stack gap="xs" align="center">
              <Text size="xl" fw={700} c="green">
                {healthOverview.healthy_services}
              </Text>
              <Text size="sm" c="dimmed">
                Healthy Services
              </Text>
              <Text size="xs" c="dimmed">
                out of {healthOverview.total_services}
              </Text>
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md" withBorder>
            <Stack gap="xs" align="center">
              <Text size="xl" fw={700} c="blue">
                {healthOverview.check_duration_ms}
              </Text>
              <Text size="sm" c="dimmed">
                Check Duration (ms)
              </Text>
              <PerformanceIcon color={theme.colors.blue[6]} />
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md" withBorder>
            <Stack gap="xs" align="center">
              <Text size="xl" fw={700}>
                {Object.keys(healthOverview.integrations).length}
              </Text>
              <Text size="sm" c="dimmed">
                Integration Types
              </Text>
              <TrendIcon color={theme.colors.blue[6]} />
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    );
  };

  return (
    <MotionPaper
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {/* Header */}
      <Box p="md" style={{ borderBottom: `1px solid ${theme.colors.gray[3]}` }}>
        <Group justify="space-between">
          <Group>
            <Title order={4}>
              Integration Health Monitor
            </Title>
            {healthOverview && (
              <Badge
                color={
                  healthOverview.status === 'healthy'
                    ? 'green'
                    : healthOverview.status === 'degraded'
                    ? 'yellow'
                    : 'red'
                }
                leftSection={getStatusIcon(healthOverview.status)}
              >
                {healthOverview.status.toUpperCase()}
              </Badge>
            )}
          </Group>
          <Group gap="xs">
            <Tooltip label="Last updated">
              <Text size="xs" c="dimmed">
                {lastUpdate.toLocaleTimeString()}
              </Text>
            </Tooltip>
            <ActionIcon size="sm" onClick={handleRefresh} disabled={loading}>
              {loading ? <Loader size={16} /> : <RefreshIcon size={16} />}
            </ActionIcon>
          </Group>
        </Group>
      </Box>

      <Box style={{ flex: 1, overflow: 'auto' }}>
        {error && (
          <Alert color="red" m="md" title="Health Check Error">
            {error}
          </Alert>
        )}

        <Accordion multiple defaultValue={['overview']}>
          {/* Overview Stats */}
          {healthOverview && (
            <Accordion.Item value="overview">
              <Accordion.Control>
                <Title order={5}>Overview Statistics</Title>
              </Accordion.Control>
              <Accordion.Panel>
                {renderOverviewStats()}
              </Accordion.Panel>
            </Accordion.Item>
          )}

          {/* Integration Details */}
          {healthOverview && showDetails && (
            <Accordion.Item value="integrations">
              <Accordion.Control>
                <Title order={5}>Integration Details</Title>
              </Accordion.Control>
              <Accordion.Panel>
                <Grid>
                  {Object.entries(healthOverview.integrations).map(([key, health]) => (
                    <Grid.Col span={{ base: 12, lg: 6 }} key={key}>
                      {renderIntegrationCard(key, health)}
                    </Grid.Col>
                  ))}
                </Grid>
              </Accordion.Panel>
            </Accordion.Item>
          )}

          {/* Detailed Health by Category */}
          {Object.keys(detailedHealth).length > 0 && (
            <Accordion.Item value="detailed">
              <Accordion.Control>
                <Title order={5}>Detailed Health Checks</Title>
              </Accordion.Control>
              <Accordion.Panel>
                <Tabs value={selectedTab.toString()} onTabChange={(value) => setSelectedTab(parseInt(value || '0'))}>
                  <Tabs.List>
                    {Object.keys(detailedHealth).map((integration, index) => (
                      <Tabs.Tab
                        key={integration}
                        value={index.toString()}
                        leftSection={getIntegrationIcon(integration)}
                      >
                        {getIntegrationName(integration)}
                      </Tabs.Tab>
                    ))}
                  </Tabs.List>

                  {Object.entries(detailedHealth).map(([integration, health], index) => (
                    <Tabs.Panel key={integration} value={index.toString()}>
                      <Card withBorder mt="md">
                        <pre style={{ fontSize: '0.875rem', overflow: 'auto', margin: 0 }}>
                          {JSON.stringify(health, null, 2)}
                        </pre>
                      </Card>
                    </Tabs.Panel>
                  ))}
                </Tabs>
              </Accordion.Panel>
            </Accordion.Item>
          )}
        </Accordion>
      </Box>
    </MotionPaper>
  );
});

IntegrationHealthMonitor.displayName = 'IntegrationHealthMonitor';
export default IntegrationHealthMonitor;