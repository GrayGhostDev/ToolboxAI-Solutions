import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Text,
  Title,
  Paper,
  Stack,
  Grid,
  Container,
  Card,
  Group,
  Badge,
  Alert,
  Select,
  ActionIcon,
  Progress,
  Skeleton,
  SimpleGrid,
} from '@mantine/core';
import {
  IconSchool,
  IconUser,
  IconTrendingUp,
  IconChartBar,
  IconTrophy,
  IconPlayerPlay,
  IconRefresh,
  IconDownload,
  IconShieldCheck,
  IconAlertTriangle,
} from '@tabler/icons-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { useAppDispatch, useAppSelector } from '../../../store';
import {
  fetchPlatformAnalytics,
  fetchPerformanceMetrics,
  fetchSubjectAnalytics,
  fetchComplianceMetrics,
  refreshAllAnalytics,
  setTimeRange,
  clearError,
} from '../../../store/slices/analyticsSlice';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

export default function Analytics() {
  const dispatch = useAppDispatch();
  const {
    platform,
    performance,
    subjects,
    compliance,
    weeklyXP,
    subjectMastery,
    loading,
    error,
    timeRange,
    lastUpdated,
  } = useAppSelector((state) => state.analytics);

  const [selectedTab, setSelectedTab] = useState(0);

  useEffect(() => {
    // Load all analytics data on mount
    dispatch(refreshAllAnalytics(timeRange));
  }, [dispatch, timeRange]);

  const handleTimeRangeChange = (newRange: string | null) => {
    if (newRange) {
      dispatch(setTimeRange(newRange));
      dispatch(refreshAllAnalytics(newRange));
    }
  };

  const handleRefresh = () => {
    dispatch(refreshAllAnalytics(timeRange));
  };

  const handleExport = () => {
    // Generate CSV or PDF report
    const data = {
      platform,
      performance,
      subjects,
      compliance,
      timestamp: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-report-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
  };

  const StatCard = ({ title, value, subtitle, icon, color }: any) => (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Group justify="space-between" align="center">
        <Box>
          <Text size="sm" c="dimmed" fw={500}>
            {title}
          </Text>
          <Title order={3} style={{ color }}>
            {value}
          </Title>
          {subtitle && (
            <Text size="xs" c="dimmed">
              {subtitle}
            </Text>
          )}
        </Box>
        <Box
          style={{
            backgroundColor: color + '15',
            borderRadius: 8,
            padding: 12,
            display: 'flex',
            alignItems: 'center',
            color,
          }}
        >
          {icon}
        </Box>
      </Group>
    </Card>
  );

  if (loading && !platform) {
    return (
      <Box style={{ padding: 24 }}>
        <Stack gap="lg">
          <Skeleton height={60} />
          <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="lg">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={`skeleton-grid-${i}`} height={140} />
            ))}
          </SimpleGrid>
          <Skeleton height={400} />
        </Stack>
      </Box>
    );
  }

  return (
    <Box>
      <Group justify="space-between" align="center" mb="lg">
        <Title order={2}>Platform Analytics</Title>
        <Group gap="md">
          <Select
            label="Time Range"
            value={timeRange}
            onChange={handleTimeRangeChange}
            data={[
              { value: '7d', label: 'Last 7 days' },
              { value: '30d', label: 'Last 30 days' },
              { value: '90d', label: 'Last 90 days' },
              { value: '1y', label: 'Last year' },
            ]}
            style={{ minWidth: 120 }}
          />
          <ActionIcon onClick={handleRefresh} disabled={loading} size="lg" variant="light">
            <IconRefresh />
          </ActionIcon>
          <Button variant="outline" leftSection={<IconDownload size={16} />} onClick={handleExport}>
            Export
          </Button>
        </Group>
      </Group>

      {error && (
        <Alert
          variant="light"
          color="red"
          onClose={() => dispatch(clearError())}
          withCloseButton
          mb="lg"
        >
          {error}
        </Alert>
      )}

      {lastUpdated && (
        <Text size="xs" c="dimmed" mb="md">
          Last updated: {new Date(lastUpdated).toLocaleString()}
        </Text>
      )}

      {/* Overview Stats */}
      <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="lg" mb="xl">
        <StatCard
          title="Total Users"
          value={platform?.totalUsers?.toLocaleString() || '0'}
          subtitle={platform?.growthRate ? `+${platform.growthRate}% growth` : 'Loading...'}
          icon={<IconUser size={24} />}
          color="#1976d2"
        />
        <StatCard
          title="Schools"
          value={platform?.totalSchools || 0}
          subtitle="Active institutions"
          icon={<IconSchool size={24} />}
          color="#2e7d32"
        />
        <StatCard
          title="Lessons"
          value={platform?.totalLessons || 0}
          subtitle="Total available"
          icon={<IconChartBar size={24} />}
          color="#ed6c02"
        />
        <StatCard
          title="Avg Completion"
          value={`${platform?.averageCompletion || 0}%`}
          subtitle="Across all courses"
          icon={<IconTrendingUp size={24} />}
          color="#9c27b0"
        />
      </SimpleGrid>

      <Grid gutter="lg">
        {/* Top Performers */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group mb="md">
              <IconTrophy size={20} />
              <Title order={4}>Top Performers</Title>
            </Group>
            {loading ? (
              <Stack gap="md">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={`skeleton-performer-${i}`} height={60} />
                ))}
              </Stack>
            ) : (
              <Stack gap="md">
                {(performance?.topPerformers || []).slice(0, 5).map((performer, index) => (
                  <Paper key={performer.id || `performer-${index}`} p="md" withBorder>
                    <Group justify="space-between">
                      <Group gap="md">
                        <Badge
                          size="lg"
                          color={index === 0 ? 'yellow' : index < 3 ? 'blue' : 'gray'}
                        >
                          #{index + 1}
                        </Badge>
                        <Text fw={500}>{performer.name}</Text>
                      </Group>
                      <Group gap="xs">
                        <Badge variant="light">{performer.xp.toLocaleString()} XP</Badge>
                        <Badge variant="light" color="blue">Lvl {performer.level}</Badge>
                        <Badge variant="light" color="gray">{performer.badges} badges</Badge>
                      </Group>
                    </Group>
                  </Paper>
                ))}
              </Stack>
            )}
          </Card>
        </Grid.Col>

        {/* Subject Mastery */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group mb="md">
              <IconChartBar size={20} />
              <Title order={4}>Subject Mastery</Title>
            </Group>
            {loading ? (
              <Stack gap="md">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={`skeleton-subject-${i}`} height={60} />
                ))}
              </Stack>
            ) : (
              <Stack gap="md">
                {(subjects?.subjects || subjectMastery || []).map((subject: any, index: number) => (
                  <Box key={(subject as any).name || (subject as any).subject || `subject-${index}`}>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm" fw={500}>
                        {(subject as any).name || (subject as any).subject}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {(((subject as any).averageScore || (subject as any).mastery || 0) as number).toFixed(1)}%
                      </Text>
                    </Group>
                    <Progress
                      value={(subject as any).completionRate || (subject as any).mastery || 0}
                      size="md"
                      radius="xl"
                      color={
                        (((subject as any).completionRate || (subject as any).mastery || 0) as number) >= 80
                          ? 'green'
                          : (((subject as any).completionRate || (subject as any).mastery || 0) as number) >= 60
                          ? 'yellow'
                          : 'red'
                      }
                    />
                    <Text size="xs" c="dimmed" mt="xs">
                      {(((subject as any).completionRate || (subject as any).mastery || 0) as number).toFixed(1)}% mastery
                    </Text>
                  </Box>
                ))}
              </Stack>
            )}
          </Card>
        </Grid.Col>

        {/* Roblox Engagement */}
        <Grid.Col span={12}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group mb="md">
              <IconPlayerPlay size={20} />
              <Title order={4}>Roblox Engagement Analytics</Title>
            </Group>
            <SimpleGrid cols={{ base: 1, md: 3 }} spacing="lg">
              <Paper p="md" withBorder style={{ textAlign: 'center' }}>
                <Title order={3} c="blue" fw={700}>
                  {platform?.activeUsers?.toLocaleString() || '0'}
                </Title>
                <Text c="dimmed">Active Users Today</Text>
              </Paper>
              <Paper p="md" withBorder style={{ textAlign: 'center' }}>
                <Title order={3} c="gray" fw={700}>
                  {platform?.averageEngagement || 0}%
                </Title>
                <Text c="dimmed">Engagement Rate</Text>
              </Paper>
              <Paper p="md" withBorder>
                <Text fw={600} mb="sm">
                  Popular Worlds
                </Text>
                <Stack gap="xs">
                  {['Math Adventure', 'Science Lab', 'History Quest'].map((world, index) => (
                    <Badge
                      key={`world-${index}`}
                      size="lg"
                      variant="outline"
                      fullWidth
                    >
                      {world}
                    </Badge>
                  ))}
                </Stack>
              </Paper>
            </SimpleGrid>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
}