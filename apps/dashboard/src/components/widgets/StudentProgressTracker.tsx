import React, { useEffect, useState } from 'react';
import {
  Card,
  Grid,
  Text,
  Box,
  Progress,
  Avatar,
  Stack,
  Badge,
  Paper,
  Table,
  ActionIcon,
  Tooltip,
  Loader,
  TextInput,
  Modal,
  Button,
  Group,
  Divider,
} from '@mantine/core';
import {
  IconTrendingUp,
  IconTrendingDown,
  IconSchool,
  IconTrophy,
  IconCheck,
  IconAlertTriangle,
  IconSearch,
  IconRefresh,
  IconEye,
  IconFileText,
  IconTimeline,
  IconX,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { usePusherContext } from '../PusherProvider';
import { pusherClient } from '../../services/pusher-client';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';

interface Student {
  id: string;
  name: string;
  avatar?: string;
  grade: number;
  overallProgress: number;
  xp: number;
  level: number;
  streak: number;
  lastActive: string;
  subjects: {
    name: string;
    progress: number;
    lastScore: number;
  }[];
  badges: string[];
  status: 'online' | 'offline' | 'idle';
}

interface ProgressMetrics {
  totalStudents: number;
  averageProgress: number;
  topPerformers: number;
  needsAttention: number;
  activeNow: number;
}

const StudentProgressTracker: React.FunctionComponent<Record<string, any>> = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isConnected } = usePusherContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [studentDetailsOpen, setStudentDetailsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const refetch = () => {
    setLoading(true);
    // Simulate data refresh
    setTimeout(() => setLoading(false), 1000);
  };

  const [metrics, setMetrics] = useState<ProgressMetrics>({
    totalStudents: 0,
    averageProgress: 0,
    topPerformers: 0,
    needsAttention: 0,
    activeNow: 0,
  });

  const [students, setStudents] = useState<Student[]>([]);

  // Subscribe to Pusher channels for real-time student progress updates
  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to student-progress channel
    const progressChannel = pusherClient.subscribe('student-progress');

    if (progressChannel) {
      // Bind to student progress update events
      pusherClient.bind('student-progress', 'student-update', (data: any) => {
        console.log('Student progress updated:', data);
        setStudents(prev =>
          prev.map(student =>
            student.id === data.studentId
              ? { ...student, ...data.updates }
              : student
          )
        );
      });

      // Bind to metrics update events
      pusherClient.bind('student-progress', 'metrics-update', (data: any) => {
        console.log('Progress metrics updated:', data);
        setMetrics(data.metrics);
      });

      // Bind to new student events
      pusherClient.bind('student-progress', 'new-student', (data: any) => {
        console.log('New student added:', data);
        setStudents(prev => [...prev, data.student]);
      });
    }

    // Cleanup function
    return () => {
      if (progressChannel) {
        pusherClient.unbind('student-progress', 'student-update');
        pusherClient.unbind('student-progress', 'metrics-update');
        pusherClient.unbind('student-progress', 'new-student');
        pusherClient.unsubscribe('student-progress');
      }
    };
  }, [isConnected]);

  // Initialize with mock data
  useEffect(() => {
    setStudents(mockStudents);
    setMetrics({
      totalStudents: mockStudents.length,
      averageProgress: 72,
      topPerformers: 3,
      needsAttention: 2,
      activeNow: 5,
    });
  }, []);

  // Mock data for demonstration
  const mockStudents: Student[] = [
    {
      id: '1',
      name: 'Alice Johnson',
      grade: 8,
      overallProgress: 92,
      xp: 2450,
      level: 24,
      streak: 15,
      lastActive: '2 minutes ago',
      subjects: [
        { name: 'Math', progress: 95, lastScore: 98 },
        { name: 'Science', progress: 88, lastScore: 85 },
        { name: 'English', progress: 93, lastScore: 90 },
      ],
      badges: ['Top Performer', 'Perfect Week', 'Math Wizard'],
      status: 'online',
    },
    {
      id: '2',
      name: 'Bob Smith',
      grade: 8,
      overallProgress: 78,
      xp: 1820,
      level: 18,
      streak: 7,
      lastActive: '1 hour ago',
      subjects: [
        { name: 'Math', progress: 75, lastScore: 72 },
        { name: 'Science', progress: 82, lastScore: 88 },
        { name: 'English', progress: 77, lastScore: 75 },
      ],
      badges: ['Consistent Learner', 'Science Explorer'],
      status: 'idle',
    },
    {
      id: '3',
      name: 'Charlie Brown',
      grade: 7,
      overallProgress: 65,
      xp: 1350,
      level: 13,
      streak: 3,
      lastActive: '3 hours ago',
      subjects: [
        { name: 'Math', progress: 62, lastScore: 58 },
        { name: 'Science', progress: 70, lastScore: 68 },
        { name: 'English', progress: 63, lastScore: 65 },
      ],
      badges: ['Getting Started'],
      status: 'offline',
    },
    {
      id: '4',
      name: 'Diana Prince',
      grade: 9,
      overallProgress: 88,
      xp: 2680,
      level: 26,
      streak: 21,
      lastActive: '5 minutes ago',
      subjects: [
        { name: 'Math', progress: 90, lastScore: 92 },
        { name: 'Science', progress: 85, lastScore: 88 },
        { name: 'English', progress: 89, lastScore: 87 },
      ],
      badges: ['Streak Master', 'All-Rounder', 'Top 10%'],
      status: 'online',
    },
    {
      id: '5',
      name: 'Eve Wilson',
      grade: 7,
      overallProgress: 55,
      xp: 980,
      level: 9,
      streak: 1,
      lastActive: '1 day ago',
      subjects: [
        { name: 'Math', progress: 48, lastScore: 45 },
        { name: 'Science', progress: 60, lastScore: 62 },
        { name: 'English', progress: 57, lastScore: 55 },
      ],
      badges: [],
      status: 'offline',
    },
  ];

  // Filter students based on search
  const filteredStudents = students.filter(student =>
    student.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get progress color
  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'success';
    if (progress >= 60) return 'warning';
    return 'error';
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return '#4caf50';
      case 'idle': return '#ff9800';
      case 'offline': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  return (
    <Box>
      {/* Metrics Cards */}
      <Grid mb="lg">
        <Grid.Col span={{ base: 12, sm: 6, md: 2.4 }}>
          <Card shadow="sm" p="md" ta="center">
            <Text size="sm" c="dimmed" mb="xs">
              Total Students
            </Text>
            <Text size="xl" fw={700}>{metrics.totalStudents}</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 2.4 }}>
          <Card shadow="sm" p="md" ta="center">
            <Text size="sm" c="dimmed" mb="xs">
              Avg Progress
            </Text>
            <Text size="xl" fw={700} c="blue">
              {metrics.averageProgress}%
            </Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 2.4 }}>
          <Card shadow="sm" p="md" ta="center">
            <Text size="sm" c="dimmed" mb="xs">
              Top Performers
            </Text>
            <Text size="xl" fw={700} c="green">
              {metrics.topPerformers}
            </Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 2.4 }}>
          <Card shadow="sm" p="md" ta="center">
            <Text size="sm" c="dimmed" mb="xs">
              Needs Attention
            </Text>
            <Text size="xl" fw={700} c="red">
              {metrics.needsAttention}
            </Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 2.4 }}>
          <Card shadow="sm" p="md" ta="center">
            <Text size="sm" c="dimmed" mb="xs">
              Active Now
            </Text>
            <Text size="xl" fw={700} c="green">
              {metrics.activeNow}
            </Text>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Student Progress Table */}
      <Card shadow="sm" p="md">
        <Group justify="space-between" mb="md">
          <Text size="lg" fw={600}>Student Progress Tracker</Text>
          <Group gap="xs">
            <TextInput
              placeholder="Search students..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftSection={<IconSearch size={16} />}
              size="sm"
            />
            <Tooltip label="Refresh data">
              <ActionIcon
                variant="subtle"
                onClick={refetch}
              >
                <IconRefresh size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>

        {loading ? (
          <Box ta="center" p="xl">
            <Loader />
          </Box>
        ) : (
          <Table.ScrollContainer minWidth={800}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Student</Table.Th>
                  <Table.Th ta="center">Status</Table.Th>
                  <Table.Th ta="center">Overall Progress</Table.Th>
                  <Table.Th ta="center">Level</Table.Th>
                  <Table.Th ta="center">Streak</Table.Th>
                  <Table.Th ta="center">Badges</Table.Th>
                  <Table.Th ta="center">Last Active</Table.Th>
                  <Table.Th ta="center">Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredStudents.map((student) => (
                  <Table.Tr key={student.id}>
                    <Table.Td>
                      <Group gap="sm">
                        <Avatar size="sm">
                          {student.name[0]}
                        </Avatar>
                        <Box>
                          <Text size="sm" fw={500}>
                            {student.name}
                          </Text>
                          <Text size="xs" c="dimmed">
                            Grade {student.grade}
                          </Text>
                        </Box>
                      </Group>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Badge
                        size="sm"
                        style={{
                          backgroundColor: getStatusColor(student.status),
                          color: 'white',
                        }}
                      >
                        {student.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Box maw={120}>
                        <Group gap="xs" justify="center">
                          <Progress
                            value={student.overallProgress}
                            color={getProgressColor(student.overallProgress)}
                            size="sm"
                            style={{ flex: 1, minWidth: 60 }}
                          />
                          <Text size="sm" fw={500}>
                            {student.overallProgress}%
                          </Text>
                        </Group>
                      </Box>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Group gap="xs" justify="center">
                        <IconTrophy size={16} color="var(--mantine-color-yellow-6)" />
                        <Text size="sm">{student.level}</Text>
                      </Group>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Group gap="xs" justify="center">
                        <Text size="sm">{student.streak}</Text>
                        <Text>🔥</Text>
                      </Group>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Text size="sm">
                        {student.badges.length > 0 ? student.badges.length : '-'}
                      </Text>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Text size="xs" c="dimmed">
                        {student.lastActive}
                      </Text>
                    </Table.Td>
                    <Table.Td ta="center">
                      <Group gap="xs" justify="center">
                        <Tooltip label="View Details">
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            onClick={() => {
                              setSelectedStudent(student);
                              setStudentDetailsOpen(true);
                            }}
                          >
                            <IconEye size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="View Assignments">
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            onClick={() => {
                              dispatch(addNotification({
                                type: 'info',
                                message: `Loading assignments for ${student.name}...`
                              }));
                              navigate(`/assessments?studentId=${student.id}&studentName=${encodeURIComponent(student.name)}`);
                            }}
                          >
                            <IconFileText size={16} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="View Timeline">
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            onClick={() => {
                              dispatch(addNotification({
                                type: 'info',
                                message: `Loading progress timeline for ${student.name}...`
                              }));
                              navigate(`/progress?studentId=${student.id}&view=timeline`);
                            }}
                          >
                            <IconTimeline size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </Card>

      {/* Connection Status */}
      {!isConnected && (
        <Box mt="md" ta="center">
          <Badge color="red" size="sm">
            Offline - Showing cached data
          </Badge>
        </Box>
      )}

      {/* Student Details Modal */}
      <Modal
        opened={studentDetailsOpen}
        onClose={() => setStudentDetailsOpen(false)}
        size="lg"
        title={
          <Group justify="space-between" w="100%">
            <Text fw={600}>
              {selectedStudent?.name} - Progress Details
            </Text>
          </Group>
        }
      >
        {selectedStudent && (
          <Stack gap="lg">
            {/* Student Overview */}
            <Group gap="md" mb="md">
              <Avatar size="xl">
                {selectedStudent.name[0]}
              </Avatar>
              <Box>
                <Text size="xl" fw={700}>{selectedStudent.name}</Text>
                <Text size="sm" c="dimmed">
                  Grade {selectedStudent.grade} • Level {selectedStudent.level}
                </Text>
                <Badge
                  mt="xs"
                  style={{
                    backgroundColor: getStatusColor(selectedStudent.status),
                    color: 'white'
                  }}
                >
                  {selectedStudent.status}
                </Badge>
              </Box>
            </Group>

            {/* Progress Metrics */}
            <Grid>
              <Grid.Col span={4}>
                <Paper p="md" ta="center">
                  <Text size="sm" c="dimmed" mb="xs">
                    Overall Progress
                  </Text>
                  <Text size="xl" fw={700} c="blue">
                    {selectedStudent.overallProgress}%
                  </Text>
                  <Progress
                    value={selectedStudent.overallProgress}
                    mt="xs"
                  />
                </Paper>
              </Grid.Col>

              <Grid.Col span={4}>
                <Paper p="md" ta="center">
                  <Text size="sm" c="dimmed" mb="xs">
                    XP Points
                  </Text>
                  <Text size="xl" fw={700}>
                    {selectedStudent.xp}
                  </Text>
                </Paper>
              </Grid.Col>

              <Grid.Col span={4}>
                <Paper p="md" ta="center">
                  <Text size="sm" c="dimmed" mb="xs">
                    Current Streak
                  </Text>
                  <Text size="xl" fw={700}>
                    {selectedStudent.streak} 🔥
                  </Text>
                </Paper>
              </Grid.Col>
            </Grid>

            {/* Subject Progress */}
            <Box>
              <Text size="lg" fw={600} mb="md">
                Subject Progress
              </Text>
              <Stack gap="md">
                {selectedStudent.subjects.map((subject, index) => (
                  <Group key={index} justify="space-between">
                    <Box>
                      <Text fw={500}>{subject.name}</Text>
                      <Text size="sm" c="dimmed">Last Score: {subject.lastScore}%</Text>
                    </Box>
                    <Box w={200}>
                      <Group gap="xs" justify="flex-end">
                        <Progress
                          value={subject.progress}
                          color={subject.progress >= 70 ? 'green' : 'yellow'}
                          style={{ flex: 1 }}
                        />
                        <Text size="sm" c="dimmed" w={40} ta="right">
                          {subject.progress}%
                        </Text>
                      </Group>
                    </Box>
                  </Group>
                ))}
              </Stack>
            </Box>

            {/* Badges */}
            {selectedStudent.badges.length > 0 && (
              <Box>
                <Text size="lg" fw={600} mb="md">
                  Badges Earned
                </Text>
                <Group gap="xs">
                  {selectedStudent.badges.map((badge, index) => (
                    <Badge key={index} variant="light">{badge}</Badge>
                  ))}
                </Group>
              </Box>
            )}

            {/* Action Buttons */}
            <Group justify="flex-end" mt="md">
              <Button
                variant="outline"
                onClick={() => {
                  setStudentDetailsOpen(false);
                  navigate(`/progress?studentId=${selectedStudent?.id}`);
                }}
              >
                View Full Progress Report
              </Button>
              <Button
                onClick={() => setStudentDetailsOpen(false)}
              >
                Close
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Box>
  );
};

export default StudentProgressTracker;
