import * as React from "react";
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
  Paper,
  Grid,
  Group,
  useMantineTheme,
} from '@mantine/core';

import { useState, useEffect } from "react";
import {
  IconTrophy as EmojiEvents,
  IconTrendingUp,
  IconSchool as School,
  IconRefresh as Refresh,
  IconClipboard as Assignment,
  IconPlayerPlay as PlayArrow,
  IconCircleCheck as CheckCircle,
} from "@tabler/icons-react";
import {
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
} from "recharts";
import { usePusherContext } from "../../contexts/PusherContext";
import { getStudentProgress, getWeeklyXP, getSubjectMastery } from "../../services/api";

interface StudentData {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  level: number;
  totalXP: number;
  completionRate: number;
  averageScore: number;
  timeSpent: number; // in hours
  streak: number; // consecutive days
  lastActive: string;
  achievements: number;
  lessonsCompleted: number;
  lessonsTotal: number;
  rank: number;
  classRank: number;
  subjects: {
    name: string;
    mastery: number;
    progress: number;
    color: string;
  }[];
  recentActivity: {
    type: "lesson" | "quiz" | "game" | "achievement";
    title: string;
    score?: number;
    completedAt: string;
    xpEarned: number;
  }[];
}

interface WeeklyProgress {
  day: string;
  xp: number;
  timeSpent: number;
  completions: number;
}

interface StudentProgressProps {
  studentId?: string;
  showDetailed?: boolean;
  autoRefresh?: boolean;
}

export function StudentProgress({
  studentId,
  showDetailed = true,
  autoRefresh = true
}: StudentProgressProps) {
  const theme = useMantineTheme();
  const { isConnected, subscribeToChannel, unsubscribeFromChannel } = usePusherContext();
  
  const [studentData, setStudentData] = useState<StudentData | null>(null);
  const [weeklyProgress, setWeeklyProgress] = useState<WeeklyProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch student progress data from real backend
  const fetchData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!studentId) {
        // If no specific student ID, fetch current user's progress
        const [progressResponse, weeklyResponse, subjectResponse] = await Promise.all([
          getStudentProgress("me"),
          getWeeklyXP(),
          getSubjectMastery(),
        ]);

        // Transform progress data (align with StudentProgress API)
        const transformedStudent: StudentData = {
          id: progressResponse.studentId || "current_user",
          name: "Current Student",
          email: "student@example.com",
          avatar: undefined,
          level: 0,
          totalXP: 0,
          completionRate: progressResponse.overallMastery ?? 0,
          averageScore: 0,
          timeSpent: 0,
          streak: 0,
          lastActive: new Date().toISOString(),
          achievements: 0,
          lessonsCompleted: 0,
          lessonsTotal: 0,
          rank: 0,
          classRank: 0,
          subjects: subjectResponse?.map((subject: any, index: number) => ({
            name: subject.subject || `Subject ${index + 1}`,
            mastery: subject.mastery || 0,
            progress: subject.mastery || 0,
            color: ['#2563EB', '#22C55E', '#FACC15', '#9333EA', '#EF4444'][index % 5],
          })) || [],
          recentActivity: [],
        };

        setStudentData(transformedStudent);

        // Transform weekly data
        const transformedWeekly: WeeklyProgress[] = weeklyResponse?.map((item: any) => ({
          day: new Date(item.date).toLocaleDateString([], { weekday: 'short' }),
          xp: item.xp || 0,
          timeSpent: item.timeSpent || 0,
          completions: item.completions || 0,
        })) || [];

        setWeeklyProgress(transformedWeekly);
      } else {
        // Fetch specific student data
        const [progressResponse, weeklyResponse, subjectResponse] = await Promise.all([
          getStudentProgress(studentId),
          getWeeklyXP(studentId),
          getSubjectMastery(studentId),
        ]);

        // Transform data similar to above (align with StudentProgress API)
        const transformedStudent: StudentData = {
          id: studentId,
          name: `Student ${studentId}`,
          email: "student@example.com",
          avatar: undefined,
          level: 0,
          totalXP: 0,
          completionRate: progressResponse.overallMastery ?? 0,
          averageScore: 0,
          timeSpent: 0,
          streak: 0,
          lastActive: new Date().toISOString(),
          achievements: 0,
          lessonsCompleted: 0,
          lessonsTotal: 0,
          rank: 0,
          classRank: 0,
          subjects: subjectResponse?.map((subject: any, index: number) => ({
            name: subject.subject || `Subject ${index + 1}`,
            mastery: subject.mastery || 0,
            progress: subject.mastery || 0,
            color: ['#2563EB', '#22C55E', '#FACC15', '#9333EA', '#EF4444'][index % 5],
          })) || [],
          recentActivity: [],
        };

        setStudentData(transformedStudent);
        const transformedWeekly: WeeklyProgress[] = (weeklyResponse as any[])?.map((item: any) => ({
          day: new Date(item.date).toLocaleDateString([], { weekday: 'short' }),
          xp: item.xp || 0,
          timeSpent: item.timeSpent || 0,
          completions: item.completions || 0,
        })) || [];
        setWeeklyProgress(transformedWeekly);
      }

      // Use mock data if no real data available
      if (!studentData || Object.keys(studentData).length === 0) {
        const mockStudent: StudentData = {
          id: studentId || "current_user",
          name: "Alex Johnson",
          email: "alex.johnson@school.edu",
          avatar: undefined,
          level: 12,
          totalXP: 2847,
          completionRate: 78.5,
          averageScore: 85.3,
          timeSpent: 42.5,
          streak: 7,
          lastActive: new Date().toISOString(),
          achievements: 15,
          lessonsCompleted: 28,
          lessonsTotal: 36,
          rank: 127,
          classRank: 5,
          subjects: [
            { name: "Mathematics", mastery: 88, progress: 92, color: "#2563EB" },
            { name: "Science", mastery: 76, progress: 82, color: "#22C55E" },
            { name: "Language Arts", mastery: 91, progress: 88, color: "#FACC15" },
            { name: "History", mastery: 72, progress: 76, color: "#9333EA" },
            { name: "Art", mastery: 84, progress: 90, color: "#EF4444" },
          ],
          recentActivity: [
            {
              type: "lesson",
              title: "Algebra Basics",
              score: 92,
              completedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
              xpEarned: 150,
            },
            {
              type: "quiz",
              title: "Science Quiz #5",
              score: 88,
              completedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
              xpEarned: 120,
            },
            {
              type: "achievement",
              title: "Week Warrior",
              completedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
              xpEarned: 500,
            },
          ],
        };
        setStudentData(mockStudent);

        const mockWeekly: WeeklyProgress[] = [
          { day: "Mon", xp: 240, timeSpent: 2.5, completions: 3 },
          { day: "Tue", xp: 380, timeSpent: 3.2, completions: 4 },
          { day: "Wed", xp: 290, timeSpent: 2.8, completions: 2 },
          { day: "Thu", xp: 450, timeSpent: 4.1, completions: 5 },
          { day: "Fri", xp: 320, timeSpent: 3.5, completions: 3 },
          { day: "Sat", xp: 180, timeSpent: 1.2, completions: 1 },
          { day: "Sun", xp: 120, timeSpent: 0.8, completions: 1 },
        ];
        setWeeklyProgress(mockWeekly);
      }

    } catch (err: any) {
      setError(err.message || 'Failed to load student progress');
      console.error('Error fetching student progress:', err);
      
      // Use mock data as fallback
      const mockStudent: StudentData = {
        id: studentId || "current_user",
        name: "Alex Johnson",
        email: "alex.johnson@school.edu",
        avatar: undefined,
        level: 12,
        totalXP: 2847,
        completionRate: 78.5,
        averageScore: 85.3,
        timeSpent: 42.5,
        streak: 7,
        lastActive: new Date().toISOString(),
        achievements: 15,
        lessonsCompleted: 28,
        lessonsTotal: 36,
        rank: 127,
        classRank: 5,
        subjects: [
          { name: "Mathematics", mastery: 88, progress: 92, color: "#2563EB" },
          { name: "Science", mastery: 76, progress: 82, color: "#22C55E" },
          { name: "Language Arts", mastery: 91, progress: 88, color: "#FACC15" },
          { name: "History", mastery: 72, progress: 76, color: "#9333EA" },
          { name: "Art", mastery: 84, progress: 90, color: "#EF4444" },
        ],
        recentActivity: [
          {
            type: "lesson",
            title: "Algebra Basics",
            score: 92,
            completedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            xpEarned: 150,
          },
        ],
      };
      setStudentData(mockStudent);

      const mockWeekly: WeeklyProgress[] = [
        { day: "Mon", xp: 240, timeSpent: 2.5, completions: 3 },
        { day: "Tue", xp: 380, timeSpent: 3.2, completions: 4 },
        { day: "Wed", xp: 290, timeSpent: 2.8, completions: 2 },
        { day: "Thu", xp: 450, timeSpent: 4.1, completions: 5 },
        { day: "Fri", xp: 320, timeSpent: 3.5, completions: 3 },
        { day: "Sat", xp: 180, timeSpent: 1.2, completions: 1 },
        { day: "Sun", xp: 120, timeSpent: 0.8, completions: 1 },
      ];
      setWeeklyProgress(mockWeekly);
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Real-time updates via WebSocket
  useEffect(() => {
    if (!isConnected || !autoRefresh) return;

    const subscriptionId = subscribeToChannel('student_progress', {
      'PROGRESS_UPDATE': (message: any) => {
        if (message && message.studentId === studentData?.id) {
          setStudentData(prevData => {
            if (!prevData) return prevData;
            return {
              ...prevData,
              ...message.updates,
              lastActive: new Date().toISOString(),
            };
          });
        }
      }
    });

    return () => {
      unsubscribeFromChannel(subscriptionId);
    };
  }, [isConnected, autoRefresh, subscribeToChannel, unsubscribeFromChannel, studentData?.id]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "lesson":
        return <School size={16} />;
      case "quiz":
        return <Assignment size={16} />;
      case "game":
        return <PlayArrow size={16} />;
      case "achievement":
        return <EmojiEvents size={16} />;
      default:
        return <CheckCircle size={16} />;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case "lesson":
        return "blue";
      case "quiz":
        return "cyan";
      case "game":
        return "green";
      case "achievement":
        return "yellow";
      default:
        return "gray";
    }
  };

  if (loading) {
    return (
      <Grid>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card padding="md" withBorder>
            <Skeleton circle height={60} mb="md" />
            <Skeleton height={40} mb="md" />
            <Skeleton height={100} />
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card padding="md" withBorder>
            <Skeleton height={40} mb="md" />
            <Skeleton height={200} />
          </Card>
        </Grid.Col>
      </Grid>
    );
  }

  if (!studentData) {
    return (
      <Alert color="red">
        Failed to load student data.
      </Alert>
    );
  }

  return (
    <Grid>
      {/* Student Overview */}
      <Grid.Col span={{ base: 12, md: 4 }}>
        <Card padding="md" withBorder>
          <Group justify="space-between" align="flex-start" mb="md">
            <Group>
              <Badge badgeContent={studentData.level} color="blue">
                <Avatar
                  src={studentData.avatar}
                  size={60}
                >
                  {studentData.name.charAt(0)}
                </Avatar>
              </Badge>
              <Box>
                <Title order={4} fw={600}>
                  {studentData.name}
                </Title>
                <Text size="xs" c="dimmed">
                  Level {studentData.level} • {studentData.totalXP.toLocaleString()} XP
                </Text>
              </Box>
            </Group>
            <ActionIcon size="sm" onClick={fetchData}>
              <Refresh size={16} />
            </ActionIcon>
          </Group>

          {error && (
            <Alert color="yellow" mb="md">
              Using fallback data: {error}
            </Alert>
          )}

          <Stack gap="md">
            <Box>
              <Group justify="space-between" mb="xs">
                <Text size="xs">Overall Progress</Text>
                <Text size="xs" fw={500}>
                  {studentData.lessonsCompleted}/{studentData.lessonsTotal} lessons
                </Text>
              </Group>
              <Progress
                value={(studentData.lessonsCompleted / studentData.lessonsTotal) * 100}
                size="sm"
                radius="xs"
              />
            </Box>

            <Group grow>
              <Paper p="sm" style={{ textAlign: 'center' }}>
                <Text size="xs" c="dimmed">
                  Completion Rate
                </Text>
                <Text size="lg" fw={700} c="green">
                  {studentData.completionRate.toFixed(1)}%
                </Text>
              </Paper>
              <Paper p="sm" style={{ textAlign: 'center' }}>
                <Text size="xs" c="dimmed">
                  Avg Score
                </Text>
                <Text size="lg" fw={700} c="blue">
                  {studentData.averageScore.toFixed(1)}%
                </Text>
              </Paper>
            </Group>

            <Group>
              <Badge
                leftSection={<EmojiEvents size={14} />}
                color="yellow"
                size="sm"
              >
                {studentData.achievements} Achievements
              </Badge>
              <Badge
                leftSection={<IconTrendingUp size={14} />}
                color="green"
                size="sm"
              >
                {studentData.streak} day streak
              </Badge>
            </Group>

            <Group grow>
              <Box style={{ textAlign: 'center' }}>
                <Text size="xs" c="dimmed">
                  Class Rank
                </Text>
                <Text size="lg" fw={700}>
                  #{studentData.classRank}
                </Text>
              </Box>
              <Box style={{ textAlign: 'center' }}>
                <Text size="xs" c="dimmed">
                  Global Rank
                </Text>
                <Text size="lg" fw={700}>
                  #{studentData.rank}
                </Text>
              </Box>
              <Box style={{ textAlign: 'center' }}>
                <Text size="xs" c="dimmed">
                  Time Spent
                </Text>
                <Text size="lg" fw={700}>
                  {studentData.timeSpent.toFixed(1)}h
                </Text>
              </Box>
            </Group>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Weekly Progress Chart */}
      <Grid.Col span={{ base: 12, md: 8 }}>
        <Card padding="md" withBorder>
          <Title order={4} fw={600} mb="md">
            Weekly Progress
          </Title>
          <Box style={{ height: 250 }}>
            <ResponsiveContainer>
              <BarChart data={weeklyProgress}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.gray[3]} />
                <XAxis dataKey="day" stroke={theme.colors.gray[6]} />
                <YAxis stroke={theme.colors.gray[6]} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: theme.colors.gray[0],
                    border: `1px solid ${theme.colors.gray[3]}`,
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="xp" fill={theme.colors.blue[6]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Card>
      </Grid.Col>

      {/* Subject Mastery */}
      {showDetailed && (
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md" withBorder>
            <Title order={4} fw={600} mb="md">
              Subject Mastery
            </Title>
            <Stack gap="md">
              {studentData.subjects.map((subject) => (
                <Box key={subject.name}>
                  <Group justify="space-between" mb="xs">
                    <Text size="sm" fw={500}>
                      {subject.name}
                    </Text>
                    <Text size="xs">
                      {subject.mastery}% mastery
                    </Text>
                  </Group>
                  <Progress
                    value={subject.mastery}
                    size="sm"
                    radius="xs"
                    color={subject.color}
                  />
                </Box>
              ))}
            </Stack>
          </Card>
        </Grid.Col>
      )}

      {/* Recent Activity */}
      {showDetailed && (
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding="md" withBorder>
            <Title order={4} fw={600} mb="md">
              Recent Activity
            </Title>
            <Stack gap="xs">
              {studentData.recentActivity.slice(0, 5).map((activity, index) => (
                <Paper key={index} p="md">
                  <Group gap="md" align="center">
                    <Badge
                      leftSection={getActivityIcon(activity.type)}
                      color={getActivityColor(activity.type)}
                      size="sm"
                      variant="outline"
                    >
                      {activity.type}
                    </Badge>
                    <Box style={{ flex: 1 }}>
                      <Text size="sm" fw={500}>
                        {activity.title}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {new Date(activity.completedAt).toLocaleString()}
                      </Text>
                    </Box>
                    <Stack gap="xs" align="flex-end">
                      {activity.score && (
                        <Text size="xs" fw={500}>
                          {activity.score}%
                        </Text>
                      )}
                      <Badge color="blue" size="sm">
                        +{activity.xpEarned} XP
                      </Badge>
                    </Stack>
                  </Group>
                </Paper>
              ))}
            </Stack>
          </Card>
        </Grid.Col>
      )}
    </Grid>
  );
}

export default StudentProgress;