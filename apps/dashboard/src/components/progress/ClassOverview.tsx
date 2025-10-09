import * as React from 'react';
import {
  Card,
  Text,
  Title,
  Box,
  Stack,
  Avatar,
  Progress,
  Badge,
  ActionIcon,
  Skeleton,
  Alert,
  Table,
  Paper,
  SimpleGrid,
  Select,
  Tooltip,
  Group,
  ScrollArea,
  Indicator
} from '@mantine/core';
import {
  IconRefresh,
  IconDownload,
  IconSettings,
  IconEye,
  IconTrendingUp,
  IconTrendingDown,
  IconMinus,
  IconAlertCircle,
  IconCheck,
  IconClock,
  IconBook,
  IconUsers,
  IconTarget
} from '@tabler/icons-react';
import { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import { fetchClassOverview, fetchStudentProgress } from '../../store/slices/progressSlice';

interface ClassOverviewProps {
  classId: string;
}

interface StudentProgressSummary {
  userId: string;
  displayName: string;
  avatarUrl?: string;
  totalLessons: number;
  completedLessons: number;
  progressPercentage: number;
  totalXP: number;
  level: number;
  lastActivity: string;
  currentStreak: number;
  weeklyProgress: number;
  status: 'active' | 'inactive' | 'struggling';
}

interface ClassMetrics {
  totalStudents: number;
  activeStudents: number;
  averageProgress: number;
  totalXPEarned: number;
  completionRate: number;
  engagementScore: number;
}

export default function ClassOverview({ classId }: ClassOverviewProps) {
  const dispatch = useAppDispatch();
  const { classOverview, loading, error } = useAppSelector((s) => s.progress);

  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'quarter'>('week');
  const [sortBy, setSortBy] = useState<'progress' | 'xp' | 'activity'>('progress');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'struggling'>('all');

  // Sample data for demonstration
  const [students] = useState<StudentProgressSummary[]>([
    {
      userId: 'user_1',
      displayName: 'Alice Johnson',
      avatarUrl: '/avatars/alice.jpg',
      totalLessons: 20,
      completedLessons: 15,
      progressPercentage: 75,
      totalXP: 1250,
      level: 8,
      lastActivity: '2 hours ago',
      currentStreak: 5,
      weeklyProgress: 25,
      status: 'active'
    },
    {
      userId: 'user_2',
      displayName: 'Bob Smith',
      avatarUrl: '/avatars/bob.jpg',
      totalLessons: 20,
      completedLessons: 12,
      progressPercentage: 60,
      totalXP: 980,
      level: 6,
      lastActivity: '1 day ago',
      currentStreak: 3,
      weeklyProgress: 15,
      status: 'active'
    },
    {
      userId: 'user_3',
      displayName: 'Carol Davis',
      avatarUrl: '/avatars/carol.jpg',
      totalLessons: 20,
      completedLessons: 8,
      progressPercentage: 40,
      totalXP: 650,
      level: 4,
      lastActivity: '3 days ago',
      currentStreak: 0,
      weeklyProgress: 5,
      status: 'struggling'
    }
  ]);

  const metrics: ClassMetrics = {
    totalStudents: students.length,
    activeStudents: students.filter(s => s.status === 'active').length,
    averageProgress: students.reduce((acc, s) => acc + s.progressPercentage, 0) / students.length,
    totalXPEarned: students.reduce((acc, s) => acc + s.totalXP, 0),
    completionRate: students.reduce((acc, s) => acc + s.completedLessons, 0) / students.reduce((acc, s) => acc + s.totalLessons, 0) * 100,
    engagementScore: 85 // Calculated metric
  };

  useEffect(() => {
    if (classId) {
      dispatch(fetchClassOverview(classId));
    }
  }, [dispatch, classId, timeRange]);

  // Filter and sort students
  const filteredStudents = React.useMemo(() => {
    let filtered = students;

    if (filterStatus !== 'all') {
      filtered = filtered.filter(s => s.status === filterStatus);
    }

    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'progress':
          return b.progressPercentage - a.progressPercentage;
        case 'xp':
          return b.totalXP - a.totalXP;
        case 'activity':
          return new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime();
        default:
          return 0;
      }
    });
  }, [students, filterStatus, sortBy]);

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'struggling': return 'red';
      default: return 'gray';
    }
  };

  // Get trend icon
  const getTrendIcon = (progress: number) => {
    if (progress > 20) return <IconTrendingUp size={16} color="green" />;
    if (progress < 10) return <IconTrendingDown size={16} color="red" />;
    return <IconMinus size={16} color="gray" />;
  };

  if (loading) {
    return (
      <Box p="xl">
        <Stack gap="md">
          <Skeleton height={60} />
          <SimpleGrid cols={4} spacing="md">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} height={120} />
            ))}
          </SimpleGrid>
          <Skeleton height={400} />
        </Stack>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p="xl">
        <Alert color="red" icon={<IconAlertCircle size={16} />} title="Error Loading Class Overview">
          <Text size="sm">{error}</Text>
      </Alert>
      </Box>
    );
  }

  return (
    <Box p="xl">
      <Stack gap="lg">
      {/* Class Overview Header */}
        <Group justify="space-between" align="center">
          <Title order={2}>
            <Group gap="sm">
              <IconUsers size={28} color="var(--mantine-color-blue-6)" />
              Class Overview
            </Group>
          </Title>

          <Group gap="md">
            <Select
              value={timeRange}
              onChange={(value) => value && setTimeRange(value as any)}
              data={[
                { value: 'week', label: 'This Week' },
                { value: 'month', label: 'This Month' },
                { value: 'quarter', label: 'This Quarter' }
              ]}
              size="sm"
            />

            <ActionIcon variant="outline" onClick={() => dispatch(fetchClassOverview(classId))}>
              <IconRefresh size={16} />
            </ActionIcon>
          </Group>
        </Group>

        {/* Metrics Cards */}
        <SimpleGrid cols={4} spacing="md">
          <Card withBorder>
            <Stack gap="sm" align="center">
              <IconUsers size={32} color="var(--mantine-color-blue-6)" />
              <Text fw={600}>Total Students</Text>
              <Text size="xl" fw={700}>{metrics.totalStudents}</Text>
              <Badge variant="outline" size="sm">
                {metrics.activeStudents} active
              </Badge>
              </Stack>
          </Card>

          <Card withBorder>
            <Stack gap="sm" align="center">
              <IconTarget size={32} color="var(--mantine-color-green-6)" />
              <Text fw={600}>Average Progress</Text>
              <Text size="xl" fw={700}>{metrics.averageProgress.toFixed(1)}%</Text>
              <Progress value={metrics.averageProgress} size="sm" w="100%" />
              </Stack>
          </Card>

          <Card withBorder>
            <Stack gap="sm" align="center">
              <IconBook size={32} color="var(--mantine-color-purple-6)" />
              <Text fw={600}>Completion Rate</Text>
              <Text size="xl" fw={700}>{metrics.completionRate.toFixed(1)}%</Text>
              <Badge color="purple" variant="outline" size="sm">
                {getTrendIcon(15)} +15% this week
              </Badge>
            </Stack>
        </Card>

          <Card withBorder>
            <Stack gap="sm" align="center">
              <IconTrendingUp size={32} color="var(--mantine-color-orange-6)" />
              <Text fw={600}>Engagement</Text>
              <Text size="xl" fw={700}>{metrics.engagementScore}%</Text>
              <Badge color="orange" variant="outline" size="sm">
                Excellent
              </Badge>
            </Stack>
        </Card>
        </SimpleGrid>

        {/* Filters and Controls */}
        <Group justify="space-between">
          <Group gap="md">
            <Select
              label="Filter by Status"
              value={filterStatus}
              onChange={(value) => value && setFilterStatus(value as any)}
              data={[
                { value: 'all', label: 'All Students' },
                { value: 'active', label: 'Active Only' },
                { value: 'struggling', label: 'Needs Help' }
              ]}
              size="sm"
            />

            <Select
              label="Sort by"
              value={sortBy}
              onChange={(value) => value && setSortBy(value as any)}
                    data={[
                { value: 'progress', label: 'Progress' },
                { value: 'xp', label: 'XP Earned' },
                { value: 'activity', label: 'Last Activity' }
              ]}
              size="sm"
            />
          </Group>

          <Group gap="sm">
            <ActionIcon variant="outline">
              <IconDownload size={16} />
            </ActionIcon>
            <ActionIcon variant="outline">
              <IconSettings size={16} />
            </ActionIcon>
          </Group>
        </Group>

        {/* Student Progress Table */}
        <Card withBorder>
          <Card.Section p="md" withBorder>
            <Group justify="space-between">
              <Title order={4}>Student Progress</Title>
              <Badge variant="outline">{filteredStudents.length} students</Badge>
            </Group>
          </Card.Section>

          <ScrollArea>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Student</Table.Th>
                  <Table.Th>Progress</Table.Th>
                  <Table.Th>Level & XP</Table.Th>
                  <Table.Th>Weekly Trend</Table.Th>
                  <Table.Th>Last Activity</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredStudents.map((student) => (
                  <Table.Tr key={student.userId}>
                    <Table.Td>
                      <Group gap="sm">
                        <Indicator
                          color={getStatusColor(student.status)}
                          size={8}
                          position="bottom-end"
                        >
                          <Avatar
                            src={student.avatarUrl}
                            alt={student.displayName}
                            size="sm"
                          />
                        </Indicator>
                        <Stack gap={2}>
                          <Text fw={500} size="sm">{student.displayName}</Text>
                          <Text size="xs" c="dimmed">
                            Streak: {student.currentStreak} days
                          </Text>
                        </Stack>
                      </Group>
                    </Table.Td>

                    <Table.Td>
                      <Stack gap={4}>
                        <Progress
                          value={student.progressPercentage}
                          size="md"
                          color="blue"
                        />
                        <Text size="xs" c="dimmed">
                          {student.completedLessons}/{student.totalLessons} lessons
                        </Text>
                      </Stack>
                    </Table.Td>

                    <Table.Td>
                      <Stack gap={4}>
                        <Group gap="xs">
                          <Badge variant="outline" size="sm">
                            Level {student.level}
                          </Badge>
                          <Text size="sm" fw={500}>
                            {student.totalXP.toLocaleString()} XP
                          </Text>
                        </Group>
                      </Stack>
                    </Table.Td>

                    <Table.Td>
                      <Group gap="xs">
                        {getTrendIcon(student.weeklyProgress)}
                        <Text
                          size="sm"
                          c={
                            student.weeklyProgress > 20 ? 'green' :
                            student.weeklyProgress < 10 ? 'red' : 'gray'
                          }
                        >
                          {student.weeklyProgress}%
                        </Text>
                      </Group>
                    </Table.Td>

                    <Table.Td>
                      <Text size="sm" c="dimmed">
                        {student.lastActivity}
                      </Text>
                    </Table.Td>

                    <Table.Td>
                      <Badge color={getStatusColor(student.status)} variant="filled" size="sm">
                        {student.status}
                      </Badge>
                    </Table.Td>

                    <Table.Td>
                      <Group gap="xs">
                        <Tooltip label="View Details">
                          <ActionIcon variant="outline" size="sm">
                            <IconEye size={14} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="Send Message">
                          <ActionIcon variant="outline" size="sm" color="blue">
                            <IconSettings size={14} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Card>

        {/* Class Performance Summary */}
        <SimpleGrid cols={2} spacing="md">
          <Card withBorder>
            <Card.Section p="md" withBorder>
              <Title order={5}>Performance Metrics</Title>
            </Card.Section>

            <Stack gap="md" p="md">
              <Group justify="space-between">
                <Text size="sm">Average Completion Rate:</Text>
                <Text fw={600}>{metrics.completionRate.toFixed(1)}%</Text>
              </Group>

              <Group justify="space-between">
                <Text size="sm">Total XP Earned:</Text>
                <Text fw={600}>{metrics.totalXPEarned.toLocaleString()}</Text>
              </Group>

              <Group justify="space-between">
                <Text size="sm">Engagement Score:</Text>
                <Group gap="xs">
                  <Text fw={600}>{metrics.engagementScore}%</Text>
                  <Badge color="green" size="sm">Excellent</Badge>
                </Group>
              </Group>

              <Progress value={metrics.engagementScore} color="green" />
            </Stack>
          </Card>

          <Card withBorder>
            <Card.Section p="md" withBorder>
              <Title order={5}>Quick Actions</Title>
            </Card.Section>

            <Stack gap="sm" p="md">
              <Button
                fullWidth
                variant="outline"
                leftSection={<IconDownload size={16} />}
              >
                Export Progress Report
              </Button>

              <Button
                fullWidth
                variant="outline"
                leftSection={<IconSettings size={16} />}
              >
                Class Settings
              </Button>

              <Button
                fullWidth
                variant="outline"
                leftSection={<IconRefresh size={16} />}
                onClick={() => dispatch(fetchClassOverview(classId))}
              >
                Refresh Data
              </Button>
                          </Stack>
          </Card>
        </SimpleGrid>
      </Stack>
    </Box>
  );
}
