import React, { useEffect, useState } from 'react';
import { Card, Grid, Text, Box, Progress, Badge, Avatar, Stack, Paper, Group, Divider } from '@mantine/core';
import {
  IconTrendingUp,
  IconTrendingDown,
  IconSchool,
  IconUsers,
  IconFileText,
  IconCheck,
  IconClock,
  IconTrophy,
} from '@tabler/icons-react';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { usePusherContext } from '../PusherProvider';
import { pusherClient } from '../../services/pusher-client';
// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: string;
}
const MetricCard: React.FunctionComponent<MetricCardProps> = ({ title, value, change, icon, color }) => {
  return (
    <Card shadow="sm" p="md" h="100%">
      <Group justify="space-between" align="flex-start">
        <Box>
          <Text size="sm" c="dimmed" mb="xs">
            {title}
          </Text>
          <Text size="xl" fw={700}>
            {value}
          </Text>
          {change !== undefined && (
            <Group gap="xs" mt="xs">
              {change >= 0 ? (
                <IconTrendingUp size={16} color="var(--mantine-color-green-6)" />
              ) : (
                <IconTrendingDown size={16} color="var(--mantine-color-red-6)" />
              )}
              <Text
                size="sm"
                c={change >= 0 ? 'green' : 'red'}
              >
                {Math.abs(change)}%
              </Text>
            </Group>
          )}
        </Box>
        <Avatar size={56} color={color}>
          {icon}
        </Avatar>
      </Group>
    </Card>
  );
};
const RealTimeAnalytics: React.FunctionComponent<Record<string, any>> = () => {
  const { isConnected } = usePusherContext();
  const [loading, setLoading] = useState(false);

  // State for real-time metrics
  const [metrics, setMetrics] = useState({
    activeUsers: 0,
    completedLessons: 0,
    averageScore: 0,
    engagementRate: 0,
  });
  const [activityData, setActivityData] = useState<any>({
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'User Activity',
        data: [65, 78, 90, 81, 86, 75, 90],
        fill: true,
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        tension: 0.4,
      },
    ],
  });
  const [performanceData, setPerformanceData] = useState<any>({
    labels: ['Math', 'Science', 'English', 'History', 'Art'],
    datasets: [
      {
        label: 'Average Performance',
        data: [85, 72, 90, 78, 88],
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
      },
    ],
  });
  const [recentActivities, setRecentActivities] = useState([
    {
      id: 1,
      user: 'Alice Johnson',
      action: 'Completed Math Quiz',
      score: 95,
      time: '2 minutes ago',
    },
    {
      id: 2,
      user: 'Bob Smith',
      action: 'Started Science Lesson',
      score: null,
      time: '5 minutes ago',
    },
    {
      id: 3,
      user: 'Charlie Brown',
      action: 'Achieved Gold Badge',
      score: null,
      time: '10 minutes ago',
    },
    {
      id: 4,
      user: 'Diana Prince',
      action: 'Submitted Assignment',
      score: 88,
      time: '15 minutes ago',
    },
  ]);

  // Subscribe to Pusher channels for real-time updates
  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to analytics channel
    const analyticsChannel = pusherClient.subscribe('analytics');

    if (analyticsChannel) {
      // Bind to metric update events
      pusherClient.bind('analytics', 'metric-update', (data: any) => {
        console.log('Analytics metrics updated:', data);
        setMetrics(prev => ({
          ...prev,
          ...data.metrics
        }));
      });

      // Bind to activity chart updates
      pusherClient.bind('analytics', 'activity-chart-update', (data: any) => {
        console.log('Activity chart updated:', data);
        setActivityData(data.chartData);
      });

      // Bind to performance chart updates
      pusherClient.bind('analytics', 'performance-chart-update', (data: any) => {
        console.log('Performance chart updated:', data);
        setPerformanceData(data.chartData);
      });

      // Bind to recent activity updates
      pusherClient.bind('analytics', 'recent-activity-update', (data: any) => {
        console.log('Recent activity updated:', data);
        setRecentActivities(prev => [data.activity, ...prev.slice(0, 3)]);
      });
    }

    // Cleanup function
    return () => {
      if (analyticsChannel) {
        pusherClient.unbind('analytics', 'metric-update');
        pusherClient.unbind('analytics', 'activity-chart-update');
        pusherClient.unbind('analytics', 'performance-chart-update');
        pusherClient.unbind('analytics', 'recent-activity-update');
        pusherClient.unsubscribe('analytics');
      }
    };
  }, [isConnected]);

  // Load initial metrics when connected
  useEffect(() => {
    if (isConnected) {
      setMetrics({
        activeUsers: Math.floor(Math.random() * 100) + 150,
        completedLessons: Math.floor(Math.random() * 50) + 200,
        averageScore: Math.floor(Math.random() * 20) + 75,
        engagementRate: Math.floor(Math.random() * 30) + 65,
      });
    }
  }, [isConnected]);
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };
  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
    },
  };
  return (
    <Box p="md">
      <Text size="xl" fw={700} mb="lg">
        Real-Time Analytics Dashboard
      </Text>
      {loading && <Progress value={100} animated mb="md" />}
      {/* Connection Status */}
      <Group gap="xs" mb="md">
        <Badge
          color={isConnected ? 'green' : 'red'}
          size="sm"
        >
          {isConnected ? 'Live Data' : 'Offline'}
        </Badge>
        {isConnected && (
          <Badge
            color="blue"
            variant="outline"
            size="sm"
          >
            Real-time Updates
          </Badge>
        )}
      </Group>
      {/* Metric Cards */}
      <Grid mb="lg">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Active Users"
            value={metrics.activeUsers}
            change={12}
            icon={<IconUsers />}
            color="green"
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Completed Lessons"
            value={metrics.completedLessons}
            change={8}
            icon={<IconCheck />}
            color="blue"
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Average Score"
            value={`${metrics.averageScore}%`}
            change={-2}
            icon={<IconSchool />}
            color="orange"
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Engagement Rate"
            value={`${metrics.engagementRate}%`}
            change={15}
            icon={<IconTrophy />}
            color="violet"
          />
        </Grid.Col>
      </Grid>
      {/* Charts Row */}
      <Grid mb="lg">
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card shadow="sm" p="md">
            <Text size="lg" fw={600} mb="md">Weekly Activity Trend</Text>
            <Box h={300}>
              <Line data={activityData} options={chartOptions} />
            </Box>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="sm" p="md">
            <Text size="lg" fw={600} mb="md">Subject Performance</Text>
            <Box h={300}>
              <Doughnut data={performanceData} options={doughnutOptions} />
            </Box>
          </Card>
        </Grid.Col>
      </Grid>
      {/* Recent Activities */}
      <Grid>
        <Grid.Col span={12}>
          <Card shadow="sm" p="md">
            <Text size="lg" fw={600} mb="md">Recent Student Activities</Text>
            <Stack gap="md">
              {recentActivities.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <Group gap="md" align="flex-start">
                    <Avatar color="blue" size="md">
                      {activity.user[0]}
                    </Avatar>
                    <Box style={{ flex: 1 }}>
                      <Group justify="space-between" align="flex-start">
                        <Box>
                          <Text fw={500}>{activity.user}</Text>
                          <Group gap="xs" align="center">
                            <Text size="sm" c="dimmed">
                              {activity.action}
                            </Text>
                            {activity.score && (
                              <Badge
                                size="sm"
                                color={activity.score >= 80 ? 'green' : 'yellow'}
                              >
                                {activity.score}%
                              </Badge>
                            )}
                          </Group>
                        </Box>
                        <Group gap="xs" align="center">
                          <IconClock size={14} />
                          <Text size="xs" c="dimmed">
                            {activity.time}
                          </Text>
                        </Group>
                      </Group>
                    </Box>
                  </Group>
                  {index < recentActivities.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
};
export default RealTimeAnalytics;
