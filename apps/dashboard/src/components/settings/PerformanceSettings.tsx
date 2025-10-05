/**
 * Performance Settings Component (Migrated to Mantine v8)
 *
 * UI for controlling performance monitoring feature flags
 * and displaying performance metrics
 */

import React from 'react';
import {
  Box,
  Card,
  Text,
  Switch,
  Select,
  Divider,
  Alert,
  Badge,
  Progress,
  Button,
  Stack,
  Grid,
  Group,
  Title,
} from '@mantine/core';
import {
  IconGauge,
  IconAlertTriangle,
  IconCircleCheck,
  IconAlertCircle,
  IconCpu,
  IconClock,
  IconTrendingUp,
  IconRefresh,
  IconX,
} from '@tabler/icons-react';
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
  const handleMonitoringToggle = (checked: boolean) => {
    featureFlags.updateFlags({ enablePerformanceMonitoring: checked });

    if (checked) {
      startMonitoring();
    } else {
      stopMonitoring();
    }
  };

  /**
   * Handle monitoring level change
   */
  const handleLevelChange = (value: string | null) => {
    if (value) {
      featureFlags.updateFlags({
        performanceMonitoringLevel: value,
      });
    }
  };

  /**
   * Get score color based on value
   */
  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'green';
    if (score >= 70) return 'yellow';
    return 'red';
  };

  /**
   * Get severity color
   */
  const getSeverityColor = (severity: string): 'red' | 'yellow' | 'blue' => {
    switch (severity) {
      case 'critical':
      case 'error':
        return 'red';
      case 'warning':
        return 'yellow';
      default:
        return 'blue';
    }
  };

  return (
    <Box>
      <Title order={2} mb="lg">
        Performance Monitoring
      </Title>

      {/* Main Settings */}
      <Card shadow="sm" p="lg" mb="md" withBorder>
        <Text size="lg" fw={600} mb="md">
          Monitoring Configuration
        </Text>

        <Grid gutter="lg">
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Switch
              label="Enable Performance Monitoring"
              checked={flags.enablePerformanceMonitoring}
              onChange={(event) => handleMonitoringToggle(event.currentTarget.checked)}
              color="blue"
            />
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6 }}>
            <Select
              label="Monitoring Level"
              value={flags.performanceMonitoringLevel}
              onChange={handleLevelChange}
              disabled={!flags.enablePerformanceMonitoring}
              data={[
                { value: 'off', label: 'Off' },
                { value: 'basic', label: 'Basic' },
                { value: 'detailed', label: 'Detailed' },
                { value: 'verbose', label: 'Verbose' },
              ]}
            />
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6 }}>
            <Switch
              label="Enable Slow API Warnings"
              checked={flags.enableSlowApiWarnings}
              onChange={(event) =>
                featureFlags.updateFlags({
                  enableSlowApiWarnings: event.currentTarget.checked,
                })
              }
              color="blue"
            />
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6 }}>
            <Switch
              label="Enable React Profiler"
              checked={flags.enableReactProfiler}
              onChange={(event) =>
                featureFlags.updateFlags({
                  enableReactProfiler: event.currentTarget.checked,
                })
              }
              color="blue"
            />
          </Grid.Col>
        </Grid>
      </Card>

      {/* Performance Status */}
      {isMonitoring && (
        <Card shadow="sm" p="lg" mb="md" withBorder>
          <Group justify="space-between" mb="md">
            <Text size="lg" fw={600}>Performance Status</Text>
            <Badge
              leftSection={<IconGauge size={14} />}
              color="green"
              size="sm"
            >
              Monitoring Active
            </Badge>
          </Group>

          {summary ? (
            <>
              {/* Performance Score */}
              <Box mb="lg">
                <Text size="sm" c="dimmed" mb="xs">
                  Overall Score
                </Text>
                <Group gap="xs" align="baseline">
                  <Text size={48} fw={700} c={getScoreColor(summary.score)}>
                    {summary.score}
                  </Text>
                  <Text size="sm" c="dimmed">
                    / 100
                  </Text>
                </Group>
                <Progress
                  value={summary.score}
                  color={getScoreColor(summary.score)}
                  size="lg"
                  radius="sm"
                  mt="xs"
                />
              </Box>

              <Divider my="md" />

              {/* Key Metrics */}
              <Grid gutter="md">
                <Grid.Col span={{ base: 6, md: 3 }}>
                  <Stack align="center" gap="xs">
                    <IconClock size={24} />
                    <Text size="xs" c="dimmed">
                      FCP
                    </Text>
                    <Text size="lg" fw={600}>
                      {summary.metrics.firstContentfulPaint.toFixed(0)}ms
                    </Text>
                  </Stack>
                </Grid.Col>

                <Grid.Col span={{ base: 6, md: 3 }}>
                  <Stack align="center" gap="xs">
                    <IconTrendingUp size={24} />
                    <Text size="xs" c="dimmed">
                      LCP
                    </Text>
                    <Text size="lg" fw={600}>
                      {summary.metrics.largestContentfulPaint.toFixed(0)}ms
                    </Text>
                  </Stack>
                </Grid.Col>

                <Grid.Col span={{ base: 6, md: 3 }}>
                  <Stack align="center" gap="xs">
                    <IconCpu size={24} />
                    <Text size="xs" c="dimmed">
                      Memory
                    </Text>
                    <Text size="lg" fw={600}>
                      {summary.systemHealth.memory_usage}MB
                    </Text>
                  </Stack>
                </Grid.Col>

                <Grid.Col span={{ base: 6, md: 3 }}>
                  <Stack align="center" gap="xs">
                    <IconGauge size={24} />
                    <Text size="xs" c="dimmed">
                      CPU
                    </Text>
                    <Text size="lg" fw={600}>{summary.systemHealth.cpu_usage}%</Text>
                  </Stack>
                </Grid.Col>
              </Grid>

              <Divider my="md" />

              {/* Alerts */}
              {summary.alerts.length > 0 && (
                <Box mb="md">
                  <Group justify="space-between" mb="sm">
                    <Text size="md" fw={500}>Active Alerts</Text>
                    <Button
                      size="xs"
                      variant="subtle"
                      leftSection={<IconX size={14} />}
                      onClick={clearAlerts}
                    >
                      Clear All
                    </Button>
                  </Group>
                  <Stack gap="xs">
                    {summary.alerts.slice(-5).map((alert, index) => (
                      <Alert
                        key={index}
                        color={getSeverityColor(alert.severity)}
                        title={alert.message}
                        icon={
                          alert.severity === 'error' || alert.severity === 'critical' ? (
                            <IconAlertCircle size={16} />
                          ) : (
                            <IconAlertTriangle size={16} />
                          )
                        }
                      >
                        {alert.suggestion && (
                          <Text size="sm">{alert.suggestion}</Text>
                        )}
                      </Alert>
                    ))}
                  </Stack>
                </Box>
              )}

              {/* Recommendations */}
              {summary.recommendations.length > 0 && (
                <Box>
                  <Text size="md" fw={500} mb="sm">
                    Recommendations
                  </Text>
                  <Stack gap="xs">
                    {summary.recommendations.map((rec, index) => (
                      <Group key={index} gap="xs">
                        <IconCircleCheck size={16} color="var(--mantine-color-blue-6)" />
                        <Text size="sm">{rec}</Text>
                      </Group>
                    ))}
                  </Stack>
                </Box>
              )}
            </>
          ) : (
            <Stack align="center" py="xl" gap="md">
              <Text c="dimmed">
                Collecting performance data...
              </Text>
              <Progress value={100} animated size="sm" w="100%" />
            </Stack>
          )}
        </Card>
      )}

      {/* Not Monitoring Message */}
      {!isMonitoring && flags.enablePerformanceMonitoring && (
        <Alert color="blue" title="Performance Monitoring Ready">
          Performance monitoring is enabled but not currently active.
          <Button
            size="xs"
            variant="light"
            leftSection={<IconGauge size={14} />}
            onClick={startMonitoring}
            mt="sm"
          >
            Start Monitoring
          </Button>
        </Alert>
      )}

      {/* Disabled Message */}
      {!flags.enablePerformanceMonitoring && (
        <Alert color="yellow" title="Performance Monitoring Disabled">
          Enable performance monitoring to track application metrics and identify optimization
          opportunities.
        </Alert>
      )}
    </Box>
  );
}
