/**
 * StudentProgressDashboard Component
 * 
 * Real-time monitoring of student progress in Roblox educational environments
 * Displays individual and class-wide metrics with live updates
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  Text,
  Grid,
  Avatar,
  Group,
  Badge,
  ActionIcon,
  Button,
  Progress,
  Loader,
  Table,
  Paper,
  Tooltip,
  Stack,
  Alert,
  Title,
  SegmentedControl,
  TextInput,
  Menu
} from '@mantine/core';
import { useMantineTheme } from '@mantine/hooks';
import {
  IconSchool,
  IconUser,
  IconUsers,
  IconTrendingUp,
  IconTrendingDown,
  IconClock,
  IconCircleCheck,
  IconAlertTriangle,
  IconExclamationMark,
  IconRefresh,
  IconFilter,
  IconSearch,
  IconGrid3x3,
  IconTable,
  IconDots,
  IconEye,
  IconMessage,
  IconHelp,
  IconStar,
  IconTrophy,
  IconFlame,
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconNotes,
  IconQuestionMark,
  IconGauge,
  IconCircle
} from '@tabler/icons-react';
import { usePusherContext } from '../../contexts/PusherContext';
import { ProgressUpdate, WebSocketMessageType } from '../../types/websocket';

interface StudentProgress {
  userId: string;
  username: string;
  avatar?: string;
  status: 'online' | 'offline' | 'idle' | 'active';
  currentActivity?: string;
  location?: string;
  sessionDuration: number;
  progress: {
    overall: number;
    objectives: Array<{
      id: string;
      name: string;
      completed: boolean;
      progress: number;
    }>;
    quizzes: Array<{
      id: string;
      name: string;
      score: number;
      attempts: number;
      completed: boolean;
    }>;
  };
  metrics: {
    engagement: number;
    accuracy: number;
    speed: number;
    collaboration: number;
    streak: number;
  };
  achievements: string[];
  needsHelp: boolean;
  lastUpdate: Date;
}

interface ClassMetrics {
  totalStudents: number;
  activeStudents: number;
  averageProgress: number;
  averageEngagement: number;
  completionRate: number;
  topPerformers: string[];
  strugglingStudents: string[];
}

type ViewMode = 'grid' | 'table';
type SortField = 'username' | 'progress' | 'engagement' | 'lastUpdate';
type SortOrder = 'asc' | 'desc';

const getStatusColor = (status: StudentProgress['status']) => {
  switch (status) {
    case 'active': return 'success';
    case 'online': return 'primary';
    case 'idle': return 'warning';
    case 'offline': return 'default';
    default: return 'default';
  }
};

const getMetricColor = (value: number) => {
  if (value >= 80) return 'success';
  if (value >= 60) return 'warning';
  return 'error';
};

export const StudentProgressDashboard: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
  const { on, sendMessage, isConnected } = usePusherContext();
  
  const [students, setStudents] = useState<StudentProgress[]>([]);
  const [classMetrics, setClassMetrics] = useState<ClassMetrics | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('username');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [selectedStudent, setSelectedStudent] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // WebSocket subscriptions
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeProgress = on(WebSocketMessageType.PROGRESS_UPDATE, (data: ProgressUpdate) => {
      updateStudentProgress(data);
    });

    const unsubscribeStatus = on(WebSocketMessageType.STUDENT_STATUS, (data: any) => {
      updateStudentStatus(data);
    });

    const unsubscribeMetrics = on(WebSocketMessageType.CLASS_METRICS, (data: any) => {
      setClassMetrics(data);
    });

    // Request initial data
    sendMessage(WebSocketMessageType.REQUEST_PROGRESS, {});

    return () => {
      unsubscribeProgress();
      unsubscribeStatus();
      unsubscribeMetrics();
    };
  }, [isConnected]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !isConnected) return;

    const interval = setInterval(() => {
      sendMessage(WebSocketMessageType.REQUEST_PROGRESS, {});
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, isConnected]);

const updateStudentProgress = (update: ProgressUpdate) => {
    setStudents(prev => {
      const index = prev.findIndex(s => s.userId === update.userId);
      if (index === -1) {
        // New student
        return [...prev, createStudentFromUpdate(update)];
      }
      // Update existing student
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        progress: {
          ...updated[index].progress,
          overall: typeof update.progress === 'number' ? update.progress : updated[index].progress.overall,
          objectives: updated[index].progress.objectives,
          quizzes: updated[index].progress.quizzes,
        },
        achievements: update.achievements || updated[index].achievements,
        lastUpdate: new Date(),
      };
      return updated;
    });
  };

  const updateStudentStatus = (data: any) => {
    setStudents(prev => prev.map(student => {
      if (student.userId === data.userId) {
        return {
          ...student,
          status: data.status,
          currentActivity: data.activity,
          location: data.location
        };
      }
      return student;
    }));
  };

  const createStudentFromUpdate = (update: any): StudentProgress => ({
    userId: update.userId,
    username: update.username || `Student ${update.userId}`,
    status: 'online',
    sessionDuration: 0,
    progress: update.progress || { overall: 0, objectives: [], quizzes: [] },
    metrics: update.metrics || {
      engagement: 0,
      accuracy: 0,
      speed: 0,
      collaboration: 0,
      streak: 0
    },
    achievements: [],
    needsHelp: false,
    lastUpdate: new Date()
  });

  // Filtering and sorting
  const filteredAndSortedStudents = useMemo(() => {
    let filtered = students.filter(student =>
      student.username.toLowerCase().includes(searchQuery.toLowerCase())
    );

    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'username':
          aValue = a.username;
          bValue = b.username;
          break;
        case 'progress':
          aValue = a.progress.overall;
          bValue = b.progress.overall;
          break;
        case 'engagement':
          aValue = a.metrics.engagement;
          bValue = b.metrics.engagement;
          break;
        case 'lastUpdate':
          aValue = a.lastUpdate;
          bValue = b.lastUpdate;
          break;
        default:
          aValue = a.username;
          bValue = b.username;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [students, searchQuery, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleStudentAction = (action: string, studentId: string) => {
    switch (action) {
      case 'view':
        setSelectedStudent(studentId);
        break;
      case 'message':
        sendMessage(WebSocketMessageType.TEACHER_MESSAGE, {
          studentId,
          type: 'direct'
        });
        break;
      case 'help':
        sendMessage(WebSocketMessageType.TEACHER_INTERVENTION, {
          studentId,
          type: 'assistance'
        });
        break;
    }
    setAnchorEl(null);
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <Box style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <Card>
        <Card.Section p="md">
          <Group justify="space-between" align="center">
            <Group align="center">
              <IconSchool color={theme.colors.blue[6]} size={32} />
              <Box>
                <Title order={3}>Student Progress Dashboard</Title>
                <Text size="sm" c="dimmed">
                  Real-time monitoring of student activity and progress
                </Text>
              </Box>
            </Group>

            <Group>
              <Badge
                leftSection={<IconCircle size={8} />}
                color={isConnected ? 'green' : 'red'}
                size="sm"
              >
                {isConnected ? 'Live' : 'Offline'}
              </Badge>
              <ActionIcon
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? 'blue' : 'gray'}
              >
                <IconRefresh size={16} />
              </ActionIcon>
            </Group>
          </Group>
        </Card.Section>
      </Card>

      {/* Class Metrics */}
      {classMetrics && (
        <Grid gutter="md">
          <Grid.Col span={{ base: 6, sm: 3 }}>
            <Card>
              <Card.Section p="md">
                <Group justify="space-between" align="center">
                  <Box>
                    <Text size="xl" fw={700}>{classMetrics.activeStudents}</Text>
                    <Text size="sm" c="dimmed">Active Students</Text>
                  </Box>
                  <IconUsers color={theme.colors.blue[6]} />
                </Group>
                <Progress
                  value={(classMetrics.activeStudents / classMetrics.totalStudents) * 100}
                  mt="sm"
                />
              </Card.Section>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 6, sm: 3 }}>
            <Card>
              <Card.Section p="md">
                <Group justify="space-between" align="center">
                  <Box>
                    <Text size="xl" fw={700}>{Math.round(classMetrics.averageProgress)}%</Text>
                    <Text size="sm" c="dimmed">Avg Progress</Text>
                  </Box>
                  <IconTrendingUp color={theme.colors.green[6]} />
                </Group>
                <Progress
                  value={classMetrics.averageProgress}
                  color="green"
                  mt="sm"
                />
              </Card.Section>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 6, sm: 3 }}>
            <Card>
              <Card.Section p="md">
                <Group justify="space-between" align="center">
                  <Box>
                    <Text size="xl" fw={700}>{Math.round(classMetrics.averageEngagement)}%</Text>
                    <Text size="sm" c="dimmed">Engagement</Text>
                  </Box>
                  <IconFlame color={theme.colors.orange[6]} />
                </Group>
                <Progress
                  value={classMetrics.averageEngagement}
                  color="orange"
                  mt="sm"
                />
              </Card.Section>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 6, sm: 3 }}>
            <Card>
              <Card.Section p="md">
                <Group justify="space-between" align="center">
                  <Box>
                    <Text size="xl" fw={700}>{Math.round(classMetrics.completionRate)}%</Text>
                    <Text size="sm" c="dimmed">Completion</Text>
                  </Box>
                  <IconCircleCheck color={theme.colors.green[6]} />
                </Group>
                <Progress
                  value={classMetrics.completionRate}
                  color="green"
                  mt="sm"
                />
              </Card.Section>
            </Card>
          </Grid.Col>
        </Grid>
      )}

      {/* Controls */}
      <Card>
        <Card.Section p="md">
          <Group justify="space-between" align="center" wrap="wrap">
            <TextInput
              size="sm"
              placeholder="Search students..."
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.currentTarget.value)}
              leftSection={<IconSearch size={16} />}
              style={{ minWidth: 200 }}
            />

            <Group>
              <SegmentedControl
                value={viewMode}
                onChange={(value) => setViewMode(value as ViewMode)}
                data={[
                  { label: <IconGrid3x3 size={16} />, value: 'grid' },
                  { label: <IconTable size={16} />, value: 'table' }
                ]}
                size="sm"
              />

              <Button
                variant="outline"
                leftSection={<IconFilter size={16} />}
                size="sm"
              >
                Filters
              </Button>
            </Group>
          </Group>
        </Card.Section>
      </Card>

      {/* Student List/Grid */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {viewMode === 'grid' ? (
          <Grid container spacing={2}>
            {filteredAndSortedStudents.map((student) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={student.userId}>
                <Card
                  style={{
                    position: 'relative',
                    border: student.needsHelp ? `2px solid ${theme.colors.yellow[6]}` : `1px solid ${theme.colors.gray[3]}`,
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = theme.shadows.lg;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = theme.shadows.sm;
                  }}
                >
                  <Card.Section p="md">
                    <Group justify="space-between" align="center" mb="md">
                      <Group align="center">
                        <Box style={{ position: 'relative' }}>
                          <Avatar src={student.avatar}>
                            {student.username[0].toUpperCase()}
                          </Avatar>
                          <IconCircle
                            size={12}
                            style={{
                              position: 'absolute',
                              bottom: 0,
                              right: 0,
                              color: getStatusColor(student.status) === 'success' ? theme.colors.green[6] :
                                     getStatusColor(student.status) === 'primary' ? theme.colors.blue[6] :
                                     getStatusColor(student.status) === 'warning' ? theme.colors.yellow[6] :
                                     theme.colors.gray[4]
                            }}
                          />
                        </Box>
                        <Box>
                          <Text size="sm" fw={600}>
                            {student.username}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {student.currentActivity || 'No activity'}
                          </Text>
                        </Box>
                      </Group>

                      <ActionIcon
                        size="sm"
                        onClick={(e) => setAnchorEl(e.currentTarget)}
                      >
                        <IconDots size={16} />
                      </ActionIcon>
                    </Group>

                    <Box mb="md">
                      <Group justify="space-between" mb="xs">
                        <Text size="xs" c="dimmed">
                          Overall Progress
                        </Text>
                        <Text size="xs" fw={600}>
                          {student.progress.overall}%
                        </Text>
                      </Group>
                      <Progress
                        value={student.progress.overall}
                        color={
                          getMetricColor(student.progress.overall) === 'success' ? 'green' :
                          getMetricColor(student.progress.overall) === 'warning' ? 'yellow' : 'red'
                        }
                        size="sm"
                        radius="md"
                      />
                    </Box>

                    <Grid gutter="xs">
                      <Grid.Col span={6}>
                        <Box style={{ textAlign: 'center' }}>
                          <IconGauge size={16} color={theme.colors.gray[6]} />
                          <Text size="xs" c="dimmed" mt="xs">
                            Engagement
                          </Text>
                          <Text size="sm" fw={600}>
                            {student.metrics.engagement}%
                          </Text>
                        </Box>
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <Box style={{ textAlign: 'center' }}>
                          <IconQuestionMark size={16} color={theme.colors.gray[6]} />
                          <Text size="xs" c="dimmed" mt="xs">
                            Accuracy
                          </Text>
                          <Text size="sm" fw={600}>
                            {student.metrics.accuracy}%
                          </Text>
                        </Box>
                      </Grid.Col>
                    </Grid>

                    {student.achievements.length > 0 && (
                      <Group mt="md" gap="xs">
                        {student.achievements.slice(0, 3).map((achievement, index) => (
                          <Tooltip key={index} label={achievement}>
                            <IconTrophy size={16} color={theme.colors.yellow[6]} />
                          </Tooltip>
                        ))}
                        {student.achievements.length > 3 && (
                          <Text size="xs" c="dimmed">
                            +{student.achievements.length - 3}
                          </Text>
                        )}
                      </Group>
                    )}

                    {student.needsHelp && (
                      <Alert color="yellow" mt="md">
                        <Text size="xs">Needs assistance</Text>
                      </Alert>
                    )}
                  </Card.Section>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>
                    <Button
                      variant="subtle"
                      size="sm"
                      onClick={() => handleSort('username')}
                      rightSection={
                        sortField === 'username' ? (
                          sortOrder === 'asc' ? <IconTrendingUp size={16} /> : <IconTrendingDown size={16} />
                        ) : null
                      }
                    >
                      Student
                    </Button>
                  </Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Activity</Table.Th>
                  <Table.Th ta="center">
                    <Button
                      variant="subtle"
                      size="sm"
                      onClick={() => handleSort('progress')}
                      rightSection={
                        sortField === 'progress' ? (
                          sortOrder === 'asc' ? <IconTrendingUp size={16} /> : <IconTrendingDown size={16} />
                        ) : null
                      }
                    >
                      Progress
                    </Button>
                  </Table.Th>
                  <Table.Th ta="center">
                    <Button
                      variant="subtle"
                      size="sm"
                      onClick={() => handleSort('engagement')}
                      rightSection={
                        sortField === 'engagement' ? (
                          sortOrder === 'asc' ? <IconTrendingUp size={16} /> : <IconTrendingDown size={16} />
                        ) : null
                      }
                    >
                      Engagement
                    </Button>
                  </Table.Th>
                  <Table.Th ta="center">Accuracy</Table.Th>
                  <Table.Th ta="center">Duration</Table.Th>
                  <Table.Th ta="center">Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredAndSortedStudents.map((student) => (
                  <Table.Tr key={student.userId}>
                    <Table.Td>
                      <Group align="center">
                        <Avatar src={student.avatar} size={32}>
                          {student.username[0].toUpperCase()}
                        </Avatar>
                        <Box>
                          <Text size="sm">{student.username}</Text>
                          {student.needsHelp && (
                            <Badge color="yellow" size="sm">Needs Help</Badge>
                          )}
                        </Box>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={
                          getStatusColor(student.status) === 'success' ? 'green' :
                          getStatusColor(student.status) === 'primary' ? 'blue' :
                          getStatusColor(student.status) === 'warning' ? 'yellow' : 'gray'
                        }
                        size="sm"
                      >
                        {student.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">
                        {student.currentActivity || '-'}
                      </Text>
                      {student.location && (
                        <Text size="xs" c="dimmed">
                          @ {student.location}
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Group align="center">
                        <Progress
                          value={student.progress.overall}
                          size="sm"
                          style={{ flex: 1 }}
                        />
                        <Text size="sm">
                          {student.progress.overall}%
                        </Text>
                      </Group>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Text
                        size="sm"
                        c={
                          getMetricColor(student.metrics.engagement) === 'success' ? 'green' :
                          getMetricColor(student.metrics.engagement) === 'warning' ? 'yellow' : 'red'
                        }
                      >
                        {student.metrics.engagement}%
                      </Text>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Text size="sm">
                        {student.metrics.accuracy}%
                      </Text>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Text size="sm">
                        {formatDuration(student.sessionDuration)}
                      </Text>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Group justify="center" gap="xs">
                        <ActionIcon
                          size="sm"
                          onClick={() => handleStudentAction('view', student.userId)}
                        >
                          <IconEye size={16} />
                        </ActionIcon>
                        <ActionIcon
                          size="sm"
                          onClick={() => handleStudentAction('message', student.userId)}
                        >
                          <IconMessage size={16} />
                        </ActionIcon>
                        {student.needsHelp && (
                          <ActionIcon
                            size="sm"
                            color="yellow"
                            onClick={() => handleStudentAction('help', student.userId)}
                          >
                            <IconHelp size={16} />
                          </ActionIcon>
                        )}
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </Box>

      {/* Action Menu */}
      <Menu opened={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
        <Menu.Item
          leftSection={<IconEye size={16} />}
          onClick={() => handleStudentAction('view', selectedStudent!)}
        >
          View Details
        </Menu.Item>
        <Menu.Item
          leftSection={<IconMessage size={16} />}
          onClick={() => handleStudentAction('message', selectedStudent!)}
        >
          Send Message
        </Menu.Item>
        <Menu.Item
          leftSection={<IconHelp size={16} />}
          onClick={() => handleStudentAction('help', selectedStudent!)}
        >
          Offer Help
        </Menu.Item>
      </Menu>

      {/* Empty State */}
      {filteredAndSortedStudents.length === 0 && (
        <Box
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '16px'
          }}
        >
          <IconUsers size={64} color={theme.colors.gray[4]} />
          <Text size="lg" c="dimmed">
            No students online
          </Text>
          <Text size="sm" c="dimmed">
            Students will appear here when they join the session
          </Text>
        </Box>
      )}
    </Box>
  );
};