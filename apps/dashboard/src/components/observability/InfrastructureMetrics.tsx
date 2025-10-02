/**
 * Infrastructure Metrics Component
 *
 * Displays real-time infrastructure metrics including CPU, memory,
 * disk, network, and process information.
 */

import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Text, SimpleGrid, Progress,
  Badge, Group, Stack, Paper, RingProgress, Tooltip
} from '@mantine/core';
import {
  IconCpu, IconMemory, IconDatabase, IconNetwork,
  IconServer, IconActivity, IconAlertTriangle,
  IconCircleCheck, IconTrendingUp, IconTrendingDown
} from '@tabler/icons-react';
import { observabilityAPI } from '../../services/observability';

// Type definitions
interface SystemMetrics {
  cpu: {
    percent: number;
    count: number;
    freq_mhz: number;
  };
  memory: {
    total_gb: number;
    used_gb: number;
    available_gb: number;
    percent: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    connections: number;
  };
  uptime_seconds: number;
  timestamp: string;
}

interface ProcessMetrics {
  pid: number;
  name: string;
  status: string;
  cpu_percent: number;
  memory_mb: number;
  memory_percent: number;
  threads: number;
  file_descriptors: number;
  create_time: string;
  timestamp: string;
}

interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  warnings: string[];
  critical: string[];
  thresholds: Record<string, number>;
  timestamp: string;
}

interface InfrastructureReport {
  status: string;
  timestamp: string;
  platform: {
    system: string;
    release: string;
    version: string;
    machine: string;
    processor: string;
    python_version: string;
    hostname: string;
  };
  system: SystemMetrics;
  process: ProcessMetrics;
  threshold_check: HealthCheck;
  health_score: number;
}

// Utility functions
const formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
};

const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

const getHealthColor = (score: number): string => {
  if (score >= 90) return 'green';
  if (score >= 70) return 'yellow';
  if (score >= 50) return 'orange';
  return 'red';
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy': return 'green';
    case 'degraded': return 'yellow';
    case 'unhealthy': return 'red';
    default: return 'gray';
  }
};

// Main Component
export const InfrastructureMetrics: React.FC = () => {
  const [report, setReport] = useState<InfrastructureReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInfrastructureData = async () => {
    try {
      const response = await observabilityAPI.getInfrastructureReport();

      if (response.status === 'success') {
        setReport(response.data);
        setError(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch infrastructure metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInfrastructureData();

    // Refresh every 5 seconds
    const interval = setInterval(fetchInfrastructureData, 5000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box p="md">
        <Text>Loading infrastructure metrics...</Text>
      </Box>
    );
  }

  if (error || !report) {
    return (
      <Box p="md">
        <Text c="red">Error: {error || 'No data available'}</Text>
      </Box>
    );
  }

  return (
    <Stack gap="md">
      {/* Health Score Overview */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Group justify="space-between" mb="md">
          <Text size="lg" fw={700}>Infrastructure Health</Text>
          <Badge
            color={getStatusColor(report.threshold_check.status)}
            size="lg"
          >
            {report.threshold_check.status.toUpperCase()}
          </Badge>
        </Group>

        <Group>
          <RingProgress
            size={120}
            thickness={12}
            sections={[
              {
                value: report.health_score,
                color: getHealthColor(report.health_score)
              }
            ]}
            label={
              <Text ta="center" fw={700} size="xl">
                {report.health_score.toFixed(0)}
              </Text>
            }
          />

          <Stack gap="xs" style={{ flex: 1 }}>
            <Text size="sm" c="dimmed">
              Platform: {report.platform.system} {report.platform.release}
            </Text>
            <Text size="sm" c="dimmed">
              Hostname: {report.platform.hostname}
            </Text>
            <Text size="sm" c="dimmed">
              Uptime: {formatUptime(report.system.uptime_seconds)}
            </Text>
          </Stack>
        </Group>

        {/* Warnings and Critical Issues */}
        {(report.threshold_check.warnings.length > 0 ||
          report.threshold_check.critical.length > 0) && (
          <Stack gap="xs" mt="md">
            {report.threshold_check.critical.map((issue, idx) => (
              <Badge key={idx} color="red" leftSection={<IconAlertTriangle size={14} />}>
                {issue}
              </Badge>
            ))}
            {report.threshold_check.warnings.map((warning, idx) => (
              <Badge key={idx} color="yellow" leftSection={<IconAlertTriangle size={14} />}>
                {warning}
              </Badge>
            ))}
          </Stack>
        )}
      </Card>

      {/* System Metrics Grid */}
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md">
        {/* CPU Metrics */}
        <Card shadow="sm" padding="md" radius="md" withBorder>
          <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <IconCpu size={20} />
              <Text fw={500}>CPU</Text>
            </Group>
            <Text size="xl" fw={700} c={report.system.cpu.percent > 80 ? 'red' : 'blue'}>
              {report.system.cpu.percent.toFixed(1)}%
            </Text>
          </Group>

          <Progress
            value={report.system.cpu.percent}
            color={report.system.cpu.percent > 80 ? 'red' : 'blue'}
            size="sm"
            mb="xs"
          />

          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Cores: {report.system.cpu.count}
            </Text>
            <Text size="xs" c="dimmed">
              Freq: {report.system.cpu.freq_mhz.toFixed(0)} MHz
            </Text>
          </Stack>
        </Card>

        {/* Memory Metrics */}
        <Card shadow="sm" padding="md" radius="md" withBorder>
          <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <IconMemory size={20} />
              <Text fw={500}>Memory</Text>
            </Group>
            <Text size="xl" fw={700} c={report.system.memory.percent > 80 ? 'red' : 'green'}>
              {report.system.memory.percent.toFixed(1)}%
            </Text>
          </Group>

          <Progress
            value={report.system.memory.percent}
            color={report.system.memory.percent > 80 ? 'red' : 'green'}
            size="sm"
            mb="xs"
          />

          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Used: {report.system.memory.used_gb.toFixed(1)} GB
            </Text>
            <Text size="xs" c="dimmed">
              Total: {report.system.memory.total_gb.toFixed(1)} GB
            </Text>
          </Stack>
        </Card>

        {/* Disk Metrics */}
        <Card shadow="sm" padding="md" radius="md" withBorder>
          <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <IconDatabase size={20} />
              <Text fw={500}>Disk</Text>
            </Group>
            <Text size="xl" fw={700} c={report.system.disk.percent > 80 ? 'red' : 'cyan'}>
              {report.system.disk.percent.toFixed(1)}%
            </Text>
          </Group>

          <Progress
            value={report.system.disk.percent}
            color={report.system.disk.percent > 80 ? 'red' : 'cyan'}
            size="sm"
            mb="xs"
          />

          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Used: {report.system.disk.used_gb.toFixed(1)} GB
            </Text>
            <Text size="xs" c="dimmed">
              Free: {report.system.disk.free_gb.toFixed(1)} GB
            </Text>
          </Stack>
        </Card>

        {/* Network Metrics */}
        <Card shadow="sm" padding="md" radius="md" withBorder>
          <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <IconNetwork size={20} />
              <Text fw={500}>Network</Text>
            </Group>
            <Text size="xl" fw={700} c="violet">
              {report.system.network.connections}
            </Text>
          </Group>

          <Text size="sm" c="dimmed" mb="xs">
            Active Connections
          </Text>

          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              Sent: {formatBytes(report.system.network.bytes_sent)}
            </Text>
            <Text size="xs" c="dimmed">
              Recv: {formatBytes(report.system.network.bytes_recv)}
            </Text>
          </Stack>
        </Card>
      </SimpleGrid>

      {/* Process Metrics */}
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Group justify="space-between" mb="md">
          <Group gap="xs">
            <IconServer size={24} />
            <Text size="lg" fw={700}>Backend Process</Text>
          </Group>
          <Badge color="blue">PID: {report.process.pid}</Badge>
        </Group>

        <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
          <Paper p="sm" withBorder>
            <Text size="xs" c="dimmed" mb={4}>CPU Usage</Text>
            <Text size="lg" fw={700}>{report.process.cpu_percent.toFixed(1)}%</Text>
          </Paper>

          <Paper p="sm" withBorder>
            <Text size="xs" c="dimmed" mb={4}>Memory</Text>
            <Text size="lg" fw={700}>{report.process.memory_mb.toFixed(0)} MB</Text>
            <Text size="xs" c="dimmed">({report.process.memory_percent.toFixed(1)}%)</Text>
          </Paper>

          <Paper p="sm" withBorder>
            <Text size="xs" c="dimmed" mb={4}>Threads</Text>
            <Text size="lg" fw={700}>{report.process.threads}</Text>
          </Paper>

          <Paper p="sm" withBorder>
            <Text size="xs" c="dimmed" mb={4}>File Descriptors</Text>
            <Text size="lg" fw={700}>{report.process.file_descriptors}</Text>
          </Paper>
        </SimpleGrid>

        <Group mt="md">
          <Badge color="gray" variant="light">
            Status: {report.process.status}
          </Badge>
          <Badge color="gray" variant="light">
            Name: {report.process.name}
          </Badge>
        </Group>
      </Card>
    </Stack>
  );
};

export default InfrastructureMetrics;
