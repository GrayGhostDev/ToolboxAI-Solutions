/**
 * QuizResultsAnalytics Component
 * 
 * Real-time analytics and visualization of quiz results from Roblox educational games
 * Provides detailed insights into student performance and learning outcomes
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  Text,
  Grid,
  Paper,
  Badge,
  ActionIcon,
  Button,
  Table,
  Progress,
  RingProgress,
  Stack,
  Alert,
  Tooltip,
  SegmentedControl,
  Select,
  Avatar,
  Group,
  Title,
  Loader,
  Divider,
  useMantineTheme
} from '@mantine/core';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Area,
  AreaChart
} from 'recharts';
import {
  IconHelp,
  IconChartBar,
  IconTrendingUp,
  IconTrendingDown,
  IconCircleCheck,
  IconX,
  IconClock,
  IconGauge,
  IconTrophy,
  IconDownload,
  IconRefresh,
  IconFilter,
  IconUser,
  IconUsers,
  IconQuestionMark,
  IconClipboardCheck,
  IconSchool,
  IconBrain,
  IconBulb,
  IconAlertTriangle,
  IconExclamationMark
} from '@tabler/icons-react';
import { usePusherContext } from '../../contexts/PusherContext';
import { WebSocketMessageType } from '../../types/websocket';

interface QuizResult {
  quizId: string;
  quizName: string;
  sessionId: string;
  timestamp: Date;
  subject: string;
  gradeLevel: number;
  totalQuestions: number;
  studentResults: StudentQuizResult[];
  questionAnalytics: QuestionAnalytic[];
  overallMetrics: OverallMetrics;
}

interface StudentQuizResult {
  studentId: string;
  studentName: string;
  score: number;
  percentage: number;
  timeSpent: number;
  attempts: number;
  answers: Answer[];
  completedAt: Date;
  rank?: number;
}

interface Answer {
  questionId: string;
  answer: string;
  isCorrect: boolean;
  timeSpent: number;
  attempts: number;
}

interface QuestionAnalytic {
  questionId: string;
  questionText: string;
  correctAnswer: string;
  difficulty: 'easy' | 'medium' | 'hard';
  topic: string;
  correctCount: number;
  incorrectCount: number;
  averageTime: number;
  commonWrongAnswers: Array<{ answer: string; count: number }>;
}

interface OverallMetrics {
  averageScore: number;
  medianScore: number;
  highestScore: number;
  lowestScore: number;
  completionRate: number;
  averageTimeSpent: number;
  passRate: number;
  improvementRate: number;
}

type ViewMode = 'overview' | 'students' | 'questions' | 'insights';
type ChartType = 'bar' | 'line' | 'pie' | 'radar';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0'];

export const QuizResultsAnalytics: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
  const { on, sendMessage, isConnected } = usePusherContext();
  
  const [quizResults, setQuizResults] = useState<QuizResult[]>([]);
  const [selectedQuiz, setSelectedQuiz] = useState<QuizResult | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [chartType, setChartType] = useState<ChartType>('bar');
  const [timeRange, setTimeRange] = useState<'today' | 'week' | 'month' | 'all'>('week');
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // WebSocket subscriptions
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeResults = on(WebSocketMessageType.QUIZ_RESULTS, (data: any) => {
      handleNewQuizResults(data);
    });

    const unsubscribeUpdate = on(WebSocketMessageType.QUIZ_UPDATE, (data: any) => {
      handleQuizUpdate(data);
    });

    // Request initial data
    sendMessage(WebSocketMessageType.REQUEST_QUIZ_RESULTS, { timeRange });

    return () => {
      unsubscribeResults();
      unsubscribeUpdate();
    };
  }, [isConnected, timeRange]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !isConnected) return;

    const interval = setInterval(() => {
      sendMessage(WebSocketMessageType.REQUEST_QUIZ_RESULTS, { timeRange });
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, isConnected, timeRange]);

  const handleNewQuizResults = (data: QuizResult) => {
    setQuizResults(prev => {
      const existing = prev.find(q => q.quizId === data.quizId);
      if (existing) {
        return prev.map(q => q.quizId === data.quizId ? data : q);
      }
      return [data, ...prev];
    });
  };

  const handleQuizUpdate = (data: any) => {
    if (selectedQuiz && selectedQuiz.quizId === data.quizId) {
      setSelectedQuiz(prev => prev ? { ...prev, ...data } : null);
    }
  };

  const exportResults = () => {
    if (!selectedQuiz) return;

    const csvContent = generateCSV(selectedQuiz);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quiz_results_${selectedQuiz.quizId}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const generateCSV = (quiz: QuizResult): string => {
    const headers = ['Student Name', 'Score', 'Percentage', 'Time Spent (min)', 'Attempts', 'Rank'];
    const rows = quiz.studentResults.map(student => [
      student.studentName,
      student.score,
      `${student.percentage}%`,
      Math.round(student.timeSpent / 60),
      student.attempts,
      student.rank || 'N/A'
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  };

  // Calculate insights
  const insights = useMemo(() => {
    if (!selectedQuiz) return null;

    const strugglingTopics = selectedQuiz.questionAnalytics
      .filter(q => (q.correctCount / (q.correctCount + q.incorrectCount)) < 0.5)
      .map(q => q.topic);

    const difficultQuestions = selectedQuiz.questionAnalytics
      .filter(q => (q.correctCount / (q.correctCount + q.incorrectCount)) < 0.4)
      .map(q => ({ id: q.questionId, text: q.questionText }));

    const topPerformers = selectedQuiz.studentResults
      .sort((a, b) => b.percentage - a.percentage)
      .slice(0, 3);

    const needsHelp = selectedQuiz.studentResults
      .filter(s => s.percentage < 60)
      .map(s => ({ id: s.studentId, name: s.studentName, score: s.percentage }));

    return {
      strugglingTopics: [...new Set(strugglingTopics)],
      difficultQuestions,
      topPerformers,
      needsHelp,
      averageImprovement: calculateImprovement(selectedQuiz)
    };
  }, [selectedQuiz]);

  const calculateImprovement = (quiz: QuizResult): number => {
    // Mock calculation - would compare with previous quiz results
    return Math.random() * 20 - 10; // -10% to +10% improvement
  };

  // Chart data preparation
  const scoreDistributionData = useMemo(() => {
    if (!selectedQuiz) return [];

    const ranges = [
      { range: '0-20%', min: 0, max: 20 },
      { range: '21-40%', min: 21, max: 40 },
      { range: '41-60%', min: 41, max: 60 },
      { range: '61-80%', min: 61, max: 80 },
      { range: '81-100%', min: 81, max: 100 }
    ];

    return ranges.map(range => ({
      name: range.range,
      count: selectedQuiz.studentResults.filter(
        s => s.percentage >= range.min && s.percentage <= range.max
      ).length
    }));
  }, [selectedQuiz]);

  const questionPerformanceData = useMemo(() => {
    if (!selectedQuiz) return [];

    return selectedQuiz.questionAnalytics.map((q, index) => ({
      name: `Q${index + 1}`,
      correct: q.correctCount,
      incorrect: q.incorrectCount,
      accuracy: Math.round((q.correctCount / (q.correctCount + q.incorrectCount)) * 100)
    }));
  }, [selectedQuiz]);

  const topicPerformanceData = useMemo(() => {
    if (!selectedQuiz) return [];

    const topicMap = new Map<string, { correct: number; total: number }>();
    
    selectedQuiz.questionAnalytics.forEach(q => {
      const existing = topicMap.get(q.topic) || { correct: 0, total: 0 };
      topicMap.set(q.topic, {
        correct: existing.correct + q.correctCount,
        total: existing.total + q.correctCount + q.incorrectCount
      });
    });

    return Array.from(topicMap.entries()).map(([topic, data]) => ({
      topic,
      performance: Math.round((data.correct / data.total) * 100)
    }));
  }, [selectedQuiz]);

  return (
    <Box style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <Card>
        <Card.Section p="md">
          <Group justify="space-between" align="center">
            <Group align="center">
              <IconChartBar color={theme.colors.blue[6]} size={32} />
              <Box>
                <Title order={3}>Quiz Results Analytics</Title>
                <Text size="sm" c="dimmed">
                  Comprehensive analysis of quiz performance and learning outcomes
                </Text>
              </Box>
            </Group>

            <Group>
              <Select
                size="sm"
                value={timeRange}
                onChange={(value) => setTimeRange(value as any)}
                data={[
                  { value: 'today', label: 'Today' },
                  { value: 'week', label: 'This Week' },
                  { value: 'month', label: 'This Month' },
                  { value: 'all', label: 'All Time' }
                ]}
                style={{ minWidth: 120 }}
              />

              <ActionIcon
                onClick={() => sendMessage(WebSocketMessageType.REQUEST_QUIZ_RESULTS, { timeRange })}
              >
                <IconRefresh size={16} />
              </ActionIcon>

              {selectedQuiz && (
                <Button
                  variant="outline"
                  leftSection={<IconDownload size={16} />}
                  onClick={exportResults}
                  size="sm"
                >
                  Export
                </Button>
              )}
            </Group>
          </Group>
        </Card.Section>
      </Card>

      {/* Quiz Selector */}
      <Grid gutter="md">
        <Grid.Col span={12}>
          <Card>
            <Card.Section p="md">
              <Text size="sm" fw={600} mb="sm">
                Recent Quizzes
              </Text>
              <Group gap="xs" style={{ overflowX: 'auto', paddingBottom: '8px' }}>
                {quizResults.map((quiz) => (
                  <Badge
                    key={quiz.quizId}
                    style={{ cursor: 'pointer', minWidth: 120 }}
                    onClick={() => setSelectedQuiz(quiz)}
                    color={selectedQuiz?.quizId === quiz.quizId ? 'blue' : 'gray'}
                    variant={selectedQuiz?.quizId === quiz.quizId ? 'filled' : 'outline'}
                    leftSection={<IconHelp size={12} />}
                  >
                    {quiz.quizName}
                  </Badge>
                ))}
              </Group>
            </Card.Section>
          </Card>
        </Grid.Col>
      </Grid>

      {selectedQuiz && (
        <>
          {/* View Mode Selector */}
          <Group justify="center">
            <SegmentedControl
              value={viewMode}
              onChange={(value) => setViewMode(value as ViewMode)}
              data={[
                {
                  value: 'overview',
                  label: (
                    <Group gap="xs">
                      <IconClipboardCheck size={16} />
                      <Text size="sm">Overview</Text>
                    </Group>
                  )
                },
                {
                  value: 'students',
                  label: (
                    <Group gap="xs">
                      <IconUsers size={16} />
                      <Text size="sm">Students</Text>
                    </Group>
                  )
                },
                {
                  value: 'questions',
                  label: (
                    <Group gap="xs">
                      <IconQuestionMark size={16} />
                      <Text size="sm">Questions</Text>
                    </Group>
                  )
                },
                {
                  value: 'insights',
                  label: (
                    <Group gap="xs">
                      <IconBrain size={16} />
                      <Text size="sm">Insights</Text>
                    </Group>
                  )
                }
              ]}
            />
          </Group>

          {/* Content based on view mode */}
          {viewMode === 'overview' && (
            <Grid container spacing={2}>
              {/* Key Metrics */}
              <Grid.Col span={12}>
                <Grid gutter="md">
                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Card>
                      <Card.Section p="md">
                        <Group justify="space-between" align="center">
                          <Box>
                            <Text size="xl" fw={700}>
                              {Math.round(selectedQuiz.overallMetrics.averageScore)}%
                            </Text>
                            <Text size="sm" c="dimmed">
                              Average Score
                            </Text>
                          </Box>
                          <IconSchool color={theme.colors.blue[6]} />
                        </Group>
                      </Card.Section>
                    </Card>
                  </Grid.Col>

                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Card>
                      <Card.Section p="md">
                        <Group justify="space-between" align="center">
                          <Box>
                            <Text size="xl" fw={700}>
                              {Math.round(selectedQuiz.overallMetrics.passRate)}%
                            </Text>
                            <Text size="sm" c="dimmed">
                              Pass Rate
                            </Text>
                          </Box>
                          <IconCircleCheck color={theme.colors.green[6]} />
                        </Group>
                      </Card.Section>
                    </Card>
                  </Grid.Col>

                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Card>
                      <Card.Section p="md">
                        <Group justify="space-between" align="center">
                          <Box>
                            <Text size="xl" fw={700}>
                              {Math.round(selectedQuiz.overallMetrics.completionRate)}%
                            </Text>
                            <Text size="sm" c="dimmed">
                              Completion
                            </Text>
                          </Box>
                          <IconTrophy color={theme.colors.yellow[6]} />
                        </Group>
                      </Card.Section>
                    </Card>
                  </Grid.Col>

                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Card>
                      <Card.Section p="md">
                        <Group justify="space-between" align="center">
                          <Box>
                            <Text size="xl" fw={700}>
                              {Math.round(selectedQuiz.overallMetrics.averageTimeSpent / 60)}m
                            </Text>
                            <Text size="sm" c="dimmed">
                              Avg Time
                            </Text>
                          </Box>
                          <IconClock color={theme.colors.cyan[6]} />
                        </Group>
                      </Card.Section>
                    </Card>
                  </Grid.Col>
                </Grid>
              </Grid.Col>

              {/* Score Distribution Chart */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card>
                  <Card.Section p="md">
                    <Text size="sm" fw={600} mb="sm">
                      Score Distribution
                    </Text>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={scoreDistributionData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <RechartsTooltip />
                        <Bar dataKey="count" fill={theme.colors.blue[6]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Card.Section>
                </Card>
              </Grid.Col>

              {/* Question Performance Chart */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card>
                  <Card.Section p="md">
                    <Text size="sm" fw={600} mb="sm">
                      Question Performance
                    </Text>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={questionPerformanceData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <RechartsTooltip />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="accuracy"
                          stroke={theme.colors.green[6]}
                          name="Accuracy %"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card.Section>
                </Card>
              </Grid.Col>

              {/* Topic Performance */}
              <Grid.Col span={12}>
                <Card>
                  <Card.Section p="md">
                    <Text size="sm" fw={600} mb="md">
                      Performance by Topic
                    </Text>
                    <Stack gap="md">
                      {topicPerformanceData.map((topic) => (
                        <Box key={topic.topic}>
                          <Group justify="space-between" mb="xs">
                            <Text size="sm">{topic.topic}</Text>
                            <Text size="sm" fw={600}>
                              {topic.performance}%
                            </Text>
                          </Group>
                          <Progress
                            value={topic.performance}
                            size="lg"
                            radius="md"
                            color={
                              topic.performance >= 70 ? 'green' :
                              topic.performance >= 50 ? 'yellow' : 'red'
                            }
                          />
                        </Box>
                      ))}
                    </Stack>
                  </Card.Section>
                </Card>
              </Grid.Col>
            </Grid>
          )}

          {viewMode === 'students' && (
            <Card>
              <Card.Section p="md">
                <Text size="lg" fw={600} mb="md">
                  Student Performance
                </Text>
                <Table.ScrollContainer minWidth={800}>
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Rank</Table.Th>
                        <Table.Th>Student</Table.Th>
                        <Table.Th ta="center">Score</Table.Th>
                        <Table.Th ta="center">Percentage</Table.Th>
                        <Table.Th ta="center">Time</Table.Th>
                        <Table.Th ta="center">Attempts</Table.Th>
                        <Table.Th ta="center">Status</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {selectedQuiz.studentResults
                        .sort((a, b) => b.percentage - a.percentage)
                        .map((student, index) => (
                          <Table.Tr key={student.studentId}>
                            <Table.Td>
                              {index === 0 && <IconTrophy color={theme.colors.yellow[6]} />}
                              {index === 1 && <IconTrophy color={theme.colors.gray[6]} />}
                              {index === 2 && <IconTrophy style={{ color: '#CD7F32' }} />}
                              {index > 2 && <Text size="sm">{index + 1}</Text>}
                            </Table.Td>
                            <Table.Td>
                              <Group align="center">
                                <Avatar size={32}>
                                  {student.studentName[0]}
                                </Avatar>
                                <Text size="sm">{student.studentName}</Text>
                              </Group>
                            </Table.Td>
                            <Table.Td ta="center">
                              <Text size="sm">{student.score}/{selectedQuiz.totalQuestions}</Text>
                            </Table.Td>
                            <Table.Td ta="center">
                              <Badge
                                color={
                                  student.percentage >= 80 ? 'green' :
                                  student.percentage >= 60 ? 'yellow' : 'red'
                                }
                                size="sm"
                              >
                                {student.percentage}%
                              </Badge>
                            </Table.Td>
                            <Table.Td ta="center">
                              <Text size="sm">{Math.round(student.timeSpent / 60)}m</Text>
                            </Table.Td>
                            <Table.Td ta="center">
                              <Text size="sm">{student.attempts}</Text>
                            </Table.Td>
                            <Table.Td ta="center">
                              {student.percentage >= 70 ? (
                                <IconCircleCheck color={theme.colors.green[6]} />
                              ) : (
                                <IconX color={theme.colors.red[6]} />
                              )}
                            </Table.Td>
                          </Table.Tr>
                        ))}
                    </Table.Tbody>
                  </Table>
                </Table.ScrollContainer>
              </Card.Section>
            </Card>
          )}

          {viewMode === 'questions' && (
            <Grid gutter="md">
              {selectedQuiz.questionAnalytics.map((question, index) => (
                <Grid.Col span={{ base: 12, md: 6 }} key={question.questionId}>
                  <Card>
                    <Card.Section p="md">
                      <Group justify="space-between" mb="md">
                        <Text size="sm" fw={600}>
                          Question {index + 1}
                        </Text>
                        <Badge
                          color={
                            question.difficulty === 'easy' ? 'green' :
                            question.difficulty === 'medium' ? 'yellow' : 'red'
                          }
                          size="sm"
                        >
                          {question.difficulty}
                        </Badge>
                      </Group>

                      <Text size="sm" mb="md">
                        {question.questionText}
                      </Text>

                      <Box mb="md">
                        <Text size="xs" c="dimmed">
                          Correct Answer:
                        </Text>
                        <Text size="sm" c="green">
                          {question.correctAnswer}
                        </Text>
                      </Box>

                      <Grid gutter="md">
                        <Grid.Col span={6}>
                          <Box style={{ textAlign: 'center' }}>
                            <RingProgress
                              size={80}
                              thickness={8}
                              sections={[{
                                value: (question.correctCount / (question.correctCount + question.incorrectCount)) * 100,
                                color: (question.correctCount / (question.correctCount + question.incorrectCount)) > 0.7
                                  ? 'green' : 'yellow'
                              }]}
                              label={
                                <Text size="xs" ta="center">
                                  {Math.round((question.correctCount / (question.correctCount + question.incorrectCount)) * 100)}%
                                </Text>
                              }
                            />
                            <Text size="xs" c="dimmed" mt="sm">
                              Success Rate
                            </Text>
                          </Box>
                        </Grid.Col>
                        <Grid.Col span={6}>
                          <Box>
                            <Text size="xs" c="dimmed">
                              Avg Time
                            </Text>
                            <Text size="lg" fw={600}>
                              {Math.round(question.averageTime)}s
                            </Text>
                          </Box>
                        </Grid.Col>
                      </Grid>

                      {question.commonWrongAnswers.length > 0 && (
                        <Box mt="md">
                          <Text size="xs" c="dimmed" mb="xs">
                            Common Wrong Answers:
                          </Text>
                          <Stack gap="xs">
                            {question.commonWrongAnswers.slice(0, 2).map((wrong, i) => (
                              <Text key={i} size="sm" c="red">
                                • {wrong.answer} ({wrong.count} students)
                              </Text>
                            ))}
                          </Stack>
                        </Box>
                      )}
                    </Card.Section>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          )}

          {viewMode === 'insights' && insights && (
            <Grid gutter="md">
              {/* Top Performers */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card>
                  <Card.Section p="md">
                    <Group align="center" mb="md">
                      <IconTrophy color={theme.colors.yellow[6]} />
                      <Text size="lg" fw={600}>Top Performers</Text>
                    </Group>
                    <Stack gap="md">
                      {insights.topPerformers.map((student, index) => (
                        <Box
                          key={student.studentId}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '8px',
                            borderRadius: '4px',
                            backgroundColor: theme.colors.green[0]
                          }}
                        >
                          <Group align="center">
                            <Avatar size={32}>
                              {student.studentName[0]}
                            </Avatar>
                            <Text size="sm">{student.studentName}</Text>
                          </Group>
                          <Badge
                            color="green"
                            size="sm"
                          >
                            {student.percentage}%
                          </Badge>
                        </Box>
                      ))}
                    </Stack>
                  </Card.Section>
                </Card>
              </Grid.Col>

              {/* Students Needing Help */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card>
                  <Card.Section p="md">
                    <Group align="center" mb="md">
                      <IconAlertTriangle color={theme.colors.yellow[6]} />
                      <Text size="lg" fw={600}>Needs Attention</Text>
                    </Group>
                    <Stack gap="md">
                      {insights.needsHelp.map((student) => (
                        <Box
                          key={student.id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '8px',
                            borderRadius: '4px',
                            backgroundColor: theme.colors.yellow[0]
                          }}
                        >
                          <Text size="sm">{student.name}</Text>
                          <Group align="center">
                            <Badge
                              color="yellow"
                              size="sm"
                            >
                              {student.score}%
                            </Badge>
                            <Button size="sm" variant="outline">
                              Help
                            </Button>
                          </Group>
                        </Box>
                      ))}
                    </Stack>
                  </Card.Section>
                </Card>
              </Grid.Col>

              {/* Struggling Topics */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card>
                  <Card.Section p="md">
                    <Group align="center" mb="md">
                      <IconBulb color={theme.colors.cyan[6]} />
                      <Text size="lg" fw={600}>Topics to Review</Text>
                    </Group>
                    <Group gap="xs" wrap="wrap">
                      {insights.strugglingTopics.map((topic) => (
                        <Badge
                          key={topic}
                          color="red"
                          variant="outline"
                        >
                          {topic}
                        </Badge>
                      ))}
                    </Group>
                  </Card.Section>
                </Card>
              </Grid.Col>

              {/* Difficult Questions */}
              <Grid.Col span={{ base: 12, md: 6 }}>
                <Card>
                  <Card.Section p="md">
                    <Group align="center" mb="md">
                      <IconExclamationMark color={theme.colors.red[6]} />
                      <Text size="lg" fw={600}>Difficult Questions</Text>
                    </Group>
                    <Stack gap="xs">
                      {insights.difficultQuestions.slice(0, 3).map((q) => (
                        <Alert key={q.id} color="red">
                          <Text size="xs">
                            {q.text.substring(0, 100)}...
                          </Text>
                        </Alert>
                      ))}
                    </Stack>
                  </Card.Section>
                </Card>
              </Grid.Col>

              {/* Improvement Trend */}
              <Grid.Col span={12}>
                <Card>
                  <Card.Section p="md">
                    <Group justify="space-between" align="center">
                      <Text size="lg" fw={600}>Class Improvement</Text>
                      <Group align="center">
                        {insights.averageImprovement > 0 ? (
                          <IconTrendingUp color={theme.colors.green[6]} />
                        ) : (
                          <IconTrendingDown color={theme.colors.red[6]} />
                        )}
                        <Text
                          size="xl"
                          fw={700}
                          c={insights.averageImprovement > 0 ? 'green' : 'red'}
                        >
                          {insights.averageImprovement > 0 ? '+' : ''}
                          {insights.averageImprovement.toFixed(1)}%
                        </Text>
                      </Group>
                    </Group>
                    <Text size="sm" c="dimmed">
                      Compared to previous quiz
                    </Text>
                  </Card.Section>
                </Card>
              </Grid.Col>
            </Grid>
          )}
        </>
      )}

      {/* Empty State */}
      {quizResults.length === 0 && (
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
          <IconHelp size={64} color={theme.colors.gray[4]} />
          <Text size="lg" c="dimmed">
            No quiz results available
          </Text>
          <Text size="sm" c="dimmed">
            Quiz results will appear here after students complete assessments
          </Text>
        </Box>
      )}
    </Box>
  );
};