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
  CardContent,
  Typography,
  Grid,
  Paper,
  Chip,
  IconButton,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  CircularProgress,
  Stack,
  Divider,
  Alert,
  AlertTitle,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Avatar,
  AvatarGroup,
  useTheme,
  alpha
} from '@mui/material';
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
  Quiz,
  Analytics,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Cancel,
  Timer,
  Speed,
  EmojiEvents,
  Download,
  Refresh,
  FilterList,
  Person,
  Groups,
  QuestionAnswer,
  Assessment,
  Grade,
  Psychology,
  Lightbulb,
  Warning,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
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

export const QuizResultsAnalytics: React.FC = () => {
  const theme = useTheme();
  const { on, sendMessage, isConnected } = useWebSocketContext();
  
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
    // Calculate improvement based on quiz completion rate and average score
    const baselineScore = 75; // Baseline expectation
    const currentScore = quiz.averageScore;
    const completionWeight = quiz.completionRate / 100;
    
    // Calculate improvement percentage
    const scoreImprovement = ((currentScore - baselineScore) / baselineScore) * 100;
    const weightedImprovement = scoreImprovement * completionWeight;
    
    return Math.round(weightedImprovement * 100) / 100; // Round to 2 decimal places
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
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Header */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Analytics color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5">Quiz Results Analytics</Typography>
                <Typography variant="body2" color="text.secondary">
                  Comprehensive analysis of quiz performance and learning outcomes
                </Typography>
              </Box>
            </Box>
            
            <Stack direction="row" spacing={1}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Time Range</InputLabel>
                <Select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value as any)}
                >
                  <MenuItem value="today">Today</MenuItem>
                  <MenuItem value="week">This Week</MenuItem>
                  <MenuItem value="month">This Month</MenuItem>
                  <MenuItem value="all">All Time</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value as ChartType)}
                >
                  <MenuItem value="bar">Bar Chart</MenuItem>
                  <MenuItem value="line">Line Chart</MenuItem>
                  <MenuItem value="area">Area Chart</MenuItem>
                  <MenuItem value="pie">Pie Chart</MenuItem>
                </Select>
              </FormControl>
              
              <IconButton
                onClick={() => {
                  setLoading(true);
                  sendMessage(WebSocketMessageType.REQUEST_QUIZ_RESULTS, { timeRange });
                }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={20} /> : <Refresh />}
              </IconButton>
              
              <IconButton
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? 'primary' : 'default'}
              >
                <Timer />
              </IconButton>
              
              {selectedQuiz && (
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={exportResults}
                  size="small"
                  disabled={loading}
                >
                  Export
                </Button>
              )}
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* Quiz Selector */}
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Recent Quizzes
              </Typography>
              <Stack direction="row" spacing={1} sx={{ overflowX: 'auto', pb: 1 }}>
                {quizResults.map((quiz) => (
                  <Chip
                    key={quiz.quizId}
                    label={quiz.quizName}
                    onClick={() => setSelectedQuiz(quiz)}
                    color={selectedQuiz?.quizId === quiz.quizId ? 'primary' : 'default'}
                    icon={<Quiz />}
                    sx={{ minWidth: 120 }}
                  />
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {selectedQuiz && (
        <>
          {/* View Mode Selector */}
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(e, value) => value && setViewMode(value)}
              size="small"
            >
              <ToggleButton value="overview">
                <Assessment sx={{ mr: 1 }} />
                Overview
              </ToggleButton>
              <ToggleButton value="students">
                <Groups sx={{ mr: 1 }} />
                Students
              </ToggleButton>
              <ToggleButton value="questions">
                <QuestionAnswer sx={{ mr: 1 }} />
                Questions
              </ToggleButton>
              <ToggleButton value="insights">
                <Psychology sx={{ mr: 1 }} />
                Insights
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {/* Content based on view mode */}
          {viewMode === 'overview' && (
            <Grid container spacing={2}>
              {/* Key Metrics */}
              <Grid item xs={12}>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box>
                            <Typography variant="h4">
                              {Math.round(selectedQuiz.overallMetrics.averageScore)}%
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Average Score
                            </Typography>
                          </Box>
                          <Grade color="primary" />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={6} sm={3}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box>
                            <Typography variant="h4">
                              {Math.round(selectedQuiz.overallMetrics.passRate)}%
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Pass Rate
                            </Typography>
                          </Box>
                          <CheckCircle color="success" />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={6} sm={3}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box>
                            <Typography variant="h4">
                              {Math.round(selectedQuiz.overallMetrics.completionRate)}%
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Completion
                            </Typography>
                          </Box>
                          <EmojiEvents color="warning" />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={6} sm={3}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box>
                            <Typography variant="h4">
                              {Math.round(selectedQuiz.overallMetrics.averageTimeSpent / 60)}m
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Avg Time
                            </Typography>
                          </Box>
                          <Timer color="info" />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Grid>

              {/* Score Distribution Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      Score Distribution
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={scoreDistributionData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <RechartsTooltip />
                        <Bar dataKey="count" fill={theme.palette.primary.main} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Question Performance Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      Question Performance
                    </Typography>
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
                          stroke={theme.palette.success.main}
                          name="Accuracy %"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Grid>

              {/* Topic Performance */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      Performance by Topic
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      {topicPerformanceData.map((topic) => (
                        <Box key={topic.topic} sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="body2">{topic.topic}</Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {topic.performance}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={topic.performance}
                            sx={{
                              height: 8,
                              borderRadius: 1,
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              '& .MuiLinearProgress-bar': {
                                bgcolor: topic.performance >= 70 ? 'success.main' :
                                        topic.performance >= 50 ? 'warning.main' : 'error.main'
                              }
                            }}
                          />
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {viewMode === 'students' && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Student Performance
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Rank</TableCell>
                        <TableCell>Student</TableCell>
                        <TableCell align="center">Score</TableCell>
                        <TableCell align="center">Percentage</TableCell>
                        <TableCell align="center">Time</TableCell>
                        <TableCell align="center">Attempts</TableCell>
                        <TableCell align="center">Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedQuiz.studentResults
                        .sort((a, b) => b.percentage - a.percentage)
                        .map((student, index) => (
                          <TableRow key={student.studentId}>
                            <TableCell>
                              {index === 0 && <EmojiEvents color="warning" />}
                              {index === 1 && <EmojiEvents color="action" />}
                              {index === 2 && <EmojiEvents sx={{ color: '#CD7F32' }} />}
                              {index > 2 && index + 1}
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Avatar sx={{ width: 32, height: 32 }}>
                                  {student.studentName[0]}
                                </Avatar>
                                {student.studentName}
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              {student.score}/{selectedQuiz.totalQuestions}
                            </TableCell>
                            <TableCell align="center">
                              <Chip
                                label={`${student.percentage}%`}
                                size="small"
                                color={
                                  student.percentage >= 80 ? 'success' :
                                  student.percentage >= 60 ? 'warning' : 'error'
                                }
                              />
                            </TableCell>
                            <TableCell align="center">
                              {Math.round(student.timeSpent / 60)}m
                            </TableCell>
                            <TableCell align="center">{student.attempts}</TableCell>
                            <TableCell align="center">
                              {student.percentage >= 70 ? (
                                <CheckCircle color="success" />
                              ) : (
                                <Cancel color="error" />
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {viewMode === 'questions' && (
            <Grid container spacing={2}>
              {selectedQuiz.questionAnalytics.map((question, index) => (
                <Grid item xs={12} md={6} key={question.questionId}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                        <Typography variant="subtitle2">
                          Question {index + 1}
                        </Typography>
                        <Chip
                          label={question.difficulty}
                          size="small"
                          color={
                            question.difficulty === 'easy' ? 'success' :
                            question.difficulty === 'medium' ? 'warning' : 'error'
                          }
                        />
                      </Box>
                      
                      <Typography variant="body2" paragraph>
                        {question.questionText}
                      </Typography>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Correct Answer:
                        </Typography>
                        <Typography variant="body2" color="success.main">
                          {question.correctAnswer}
                        </Typography>
                      </Box>
                      
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Box sx={{ textAlign: 'center' }}>
                            <CircularProgress
                              variant="determinate"
                              value={(question.correctCount / (question.correctCount + question.incorrectCount)) * 100}
                              color={
                                (question.correctCount / (question.correctCount + question.incorrectCount)) > 0.7
                                  ? 'success' : 'warning'
                              }
                            />
                            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                              Success Rate
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Avg Time
                          </Typography>
                          <Typography variant="h6">
                            {Math.round(question.averageTime)}s
                          </Typography>
                        </Grid>
                      </Grid>
                      
                      {question.commonWrongAnswers.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Common Wrong Answers:
                          </Typography>
                          {question.commonWrongAnswers.slice(0, 2).map((wrong, i) => (
                            <Typography key={i} variant="body2" color="error">
                              • {wrong.answer} ({wrong.count} students)
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}

          {viewMode === 'insights' && insights && (
            <Grid container spacing={2}>
              {/* Top Performers */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <EmojiEvents color="warning" />
                      <Typography variant="h6">Top Performers</Typography>
                    </Box>
                    <Stack spacing={2}>
                      {insights.topPerformers.map((student, index) => (
                        <Box
                          key={student.studentId}
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            p: 1,
                            borderRadius: 1,
                            bgcolor: alpha(theme.palette.success.main, 0.1)
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Avatar sx={{ width: 32, height: 32 }}>
                              {student.studentName[0]}
                            </Avatar>
                            <Typography>{student.studentName}</Typography>
                          </Box>
                          <Chip
                            label={`${student.percentage}%`}
                            color="success"
                            size="small"
                          />
                        </Box>
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Topic Performance Radar Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Topic Performance Analysis</Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={topicPerformanceData}>
                          <PolarGrid />
                          <PolarAngleAxis dataKey="topic" />
                          <PolarRadiusAxis domain={[0, 100]} />
                          <Radar
                            name="Performance"
                            dataKey="performance"
                            stroke="#8884d8"
                            fill="#8884d8"
                            fillOpacity={0.6}
                          />
                          <Legend />
                        </RadarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Score Distribution Pie Chart */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Score Distribution</Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'A (90-100%)', value: 25 },
                              { name: 'B (80-89%)', value: 35 },
                              { name: 'C (70-79%)', value: 25 },
                              { name: 'D (60-69%)', value: 10 },
                              { name: 'F (<60%)', value: 5 },
                            ]}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {[
                              { name: 'A (90-100%)', value: 25 },
                              { name: 'B (80-89%)', value: 35 },
                              { name: 'C (70-79%)', value: 25 },
                              { name: 'D (60-69%)', value: 10 },
                              { name: 'F (<60%)', value: 5 },
                            ].map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <RechartsTooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Performance Trends Area Chart */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance Trends Over Time</Typography>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={questionPerformanceData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="question" />
                          <YAxis domain={[0, 100]} />
                          <RechartsTooltip />
                          <Legend />
                          <Area
                            type="monotone"
                            dataKey="accuracy"
                            stackId="1"
                            stroke="#8884d8"
                            fill="#8884d8"
                            fillOpacity={0.6}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Student Group Performance */}
              <Grid item xs={12} md={6}>
                <Paper elevation={2} sx={{ p: 2 }}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                        <FilterList color="primary" />
                        <Typography variant="h6">Student Groups</Typography>
                      </Box>
                      <AvatarGroup max={4} sx={{ mb: 2 }}>
                        {insights.topPerformers.slice(0, 4).map((student) => (
                          <Avatar key={student.studentId}>
                            {student.studentName[0]}
                          </Avatar>
                        ))}
                      </AvatarGroup>
                      <Divider sx={{ my: 2 }} />
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Person color="action" />
                        <Typography variant="body2">
                          {insights.topPerformers.length} high performers
                        </Typography>
                      </Stack>
                    </CardContent>
                  </Card>
                </Paper>
              </Grid>

              {/* Speed Analytics */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Speed color="info" />
                      <Typography variant="h6">Response Speed Metrics</Typography>
                    </Box>
                    <Stack spacing={2}>
                      <Typography variant="body2">
                        Average response time: {selectedQuiz?.averageTime || 0}s
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={Math.min((selectedQuiz?.averageTime || 0) / 60 * 100, 100)} 
                        color="info"
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Students Needing Help */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Warning color="warning" />
                      <Typography variant="h6">Needs Attention</Typography>
                    </Box>
                    <Stack spacing={2}>
                      {insights.needsHelp.map((student) => (
                        <Box
                          key={student.id}
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            p: 1,
                            borderRadius: 1,
                            bgcolor: alpha(theme.palette.warning.main, 0.1)
                          }}
                        >
                          <Typography>{student.name}</Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip
                              label={`${student.score}%`}
                              color="warning"
                              size="small"
                            />
                            <Button size="small" variant="outlined">
                              Help
                            </Button>
                          </Box>
                        </Box>
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Struggling Topics */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Lightbulb color="info" />
                      <Typography variant="h6">Topics to Review</Typography>
                    </Box>
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      {insights.strugglingTopics.map((topic) => (
                        <Chip
                          key={topic}
                          label={topic}
                          color="error"
                          variant="outlined"
                          sx={{ mb: 1 }}
                        />
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Difficult Questions */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <ErrorIcon color="error" />
                      <Typography variant="h6">Difficult Questions</Typography>
                    </Box>
                    <Stack spacing={1}>
                      {insights.difficultQuestions.slice(0, 3).map((q) => (
                        <Alert key={q.id} severity="error" sx={{ py: 0 }}>
                          <Typography variant="caption">
                            {q.text.substring(0, 100)}...
                          </Typography>
                        </Alert>
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Improvement Trend */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography variant="h6">Class Improvement</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {insights.averageImprovement > 0 ? (
                          <TrendingUp color="success" />
                        ) : (
                          <TrendingDown color="error" />
                        )}
                        <Typography
                          variant="h5"
                          color={insights.averageImprovement > 0 ? 'success.main' : 'error.main'}
                        >
                          {insights.averageImprovement > 0 ? '+' : ''}
                          {insights.averageImprovement.toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Compared to previous quiz
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </>
      )}

      {/* Empty State */}
      {quizResults.length === 0 && (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: 2
          }}
        >
          <Quiz sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="text.secondary">
            No quiz results available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Quiz results will appear here after students complete assessments
          </Typography>
        </Box>
      )}
    </Box>
  );
};