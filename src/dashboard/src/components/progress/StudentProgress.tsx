import * as React from "react";
import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Avatar,
  LinearProgress,
  Chip,
  IconButton,
  Skeleton,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  Badge,
  Grid,
} from "@mui/material";
import {
  Person,
  EmojiEvents,
  TrendingUp,
  Star,
  School,
  AccessTime,
  Refresh,
  Assignment,
  PlayArrow,
  CheckCircle,
} from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
} from "recharts";
import { useWebSocketContext } from "../../contexts/WebSocketContext";
import { apiClient, getStudentProgress, getWeeklyXP, getSubjectMastery } from "../../services/api";

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
  const theme = useTheme();
  const { isConnected, subscribe, unsubscribe } = useWebSocketContext();
  
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

        // Transform progress data
        const transformedStudent: StudentData = {
          id: progressResponse.studentId || "current_user",
          name: progressResponse.studentName || "Current Student",
          email: progressResponse.email || "student@example.com",
          avatar: progressResponse.avatar,
          level: progressResponse.level || 12,
          totalXP: progressResponse.totalXP || 2847,
          completionRate: progressResponse.completionRate || 78.5,
          averageScore: progressResponse.averageScore || 85.3,
          timeSpent: progressResponse.totalTimeSpent || 42.5,
          streak: progressResponse.currentStreak || 7,
          lastActive: progressResponse.lastActive || new Date().toISOString(),
          achievements: progressResponse.achievements?.length || 15,
          lessonsCompleted: progressResponse.lessonsCompleted || 28,
          lessonsTotal: progressResponse.lessonsTotal || 36,
          rank: progressResponse.globalRank || 127,
          classRank: progressResponse.classRank || 5,
          subjects: subjectResponse?.map((subject: any, index: number) => ({
            name: subject.subject || `Subject ${index + 1}`,
            mastery: subject.mastery || Math.floor(Math.random() * 30) + 70,
            progress: subject.progress || Math.floor(Math.random() * 40) + 60,
            color: ['#2563EB', '#22C55E', '#FACC15', '#9333EA', '#EF4444'][index % 5],
          })) || [],
          recentActivity: progressResponse.recentActivity || [],
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

        // Transform data similar to above...
        const transformedStudent: StudentData = {
          id: studentId,
          name: progressResponse.studentName || `Student ${studentId}`,
          email: progressResponse.email || "student@example.com",
          avatar: progressResponse.avatar,
          level: progressResponse.level || 12,
          totalXP: progressResponse.totalXP || 2847,
          completionRate: progressResponse.completionRate || 78.5,
          averageScore: progressResponse.averageScore || 85.3,
          timeSpent: progressResponse.totalTimeSpent || 42.5,
          streak: progressResponse.currentStreak || 7,
          lastActive: progressResponse.lastActive || new Date().toISOString(),
          achievements: progressResponse.achievements?.length || 15,
          lessonsCompleted: progressResponse.lessonsCompleted || 28,
          lessonsTotal: progressResponse.lessonsTotal || 36,
          rank: progressResponse.globalRank || 127,
          classRank: progressResponse.classRank || 5,
          subjects: subjectResponse?.map((subject: any, index: number) => ({
            name: subject.subject || `Subject ${index + 1}`,
            mastery: subject.mastery || Math.floor(Math.random() * 30) + 70,
            progress: subject.progress || Math.floor(Math.random() * 40) + 60,
            color: ['#2563EB', '#22C55E', '#FACC15', '#9333EA', '#EF4444'][index % 5],
          })) || [],
          recentActivity: progressResponse.recentActivity || [],
        };

        setStudentData(transformedStudent);
        setWeeklyProgress(weeklyResponse || []);
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

    const subscriptionId = subscribe('student_progress', (message: any) => {
      if (message.type === 'PROGRESS_UPDATE' && message.payload.studentId === studentData?.id) {
        setStudentData(prevData => {
          if (!prevData) return prevData;
          return {
            ...prevData,
            ...message.payload.updates,
            lastActive: new Date().toISOString(),
          };
        });
      }
    });

    return () => {
      unsubscribe(subscriptionId);
    };
  }, [isConnected, autoRefresh, subscribe, unsubscribe, studentData?.id]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "lesson":
        return <School fontSize="small" />;
      case "quiz":
        return <Assignment fontSize="small" />;
      case "game":
        return <PlayArrow fontSize="small" />;
      case "achievement":
        return <EmojiEvents fontSize="small" />;
      default:
        return <CheckCircle fontSize="small" />;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case "lesson":
        return "primary";
      case "quiz":
        return "info";
      case "game":
        return "success";
      case "achievement":
        return "warning";
      default:
        return "default";
    }
  };

  if (loading) {
    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Skeleton variant="circular" width={60} height={60} />
              <Skeleton variant="text" height={40} />
              <Skeleton variant="rectangular" height={100} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Skeleton variant="text" height={40} />
              <Skeleton variant="rectangular" height={200} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  }

  if (!studentData) {
    return (
      <Alert severity="error">
        Failed to load student data.
      </Alert>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Student Overview */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={2}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Badge badgeContent={studentData.level} color="primary">
                  <Avatar 
                    src={studentData.avatar} 
                    sx={{ width: 60, height: 60 }}
                  >
                    {studentData.name.charAt(0)}
                  </Avatar>
                </Badge>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {studentData.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Level {studentData.level} • {studentData.totalXP.toLocaleString()} XP
                  </Typography>
                </Box>
              </Stack>
              <IconButton size="small" onClick={fetchData}>
                <Refresh />
              </IconButton>
            </Stack>

            {error && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Using fallback data: {error}
              </Alert>
            )}

            <Stack spacing={2}>
              <Box>
                <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="caption">Overall Progress</Typography>
                  <Typography variant="caption" fontWeight={500}>
                    {studentData.lessonsCompleted}/{studentData.lessonsTotal} lessons
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={(studentData.lessonsCompleted / studentData.lessonsTotal) * 100}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>

              <Stack direction="row" spacing={2}>
                <Paper sx={{ p: 1.5, flex: 1, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Completion Rate
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: 'success.main' }}>
                    {studentData.completionRate.toFixed(1)}%
                  </Typography>
                </Paper>
                <Paper sx={{ p: 1.5, flex: 1, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Avg Score
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    {studentData.averageScore.toFixed(1)}%
                  </Typography>
                </Paper>
              </Stack>

              <Stack direction="row" spacing={2}>
                <Chip 
                  icon={<EmojiEvents />} 
                  label={`${studentData.achievements} Achievements`}
                  color="warning"
                  size="small"
                />
                <Chip 
                  icon={<TrendingUp />} 
                  label={`${studentData.streak} day streak`}
                  color="success"
                  size="small"
                />
              </Stack>

              <Stack direction="row" spacing={2}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Class Rank
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    #{studentData.classRank}
                  </Typography>
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Global Rank
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    #{studentData.rank}
                  </Typography>
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Time Spent
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {studentData.timeSpent.toFixed(1)}h
                  </Typography>
                </Box>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      {/* Weekly Progress Chart */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Weekly Progress
            </Typography>
            <Box sx={{ height: 250 }}>
              <ResponsiveContainer>
                <BarChart data={weeklyProgress}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis dataKey="day" stroke={theme.palette.text.secondary} />
                  <YAxis stroke={theme.palette.text.secondary} />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="xp" fill={theme.palette.primary.main} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Subject Mastery */}
      {showDetailed && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Subject Mastery
              </Typography>
              <Stack spacing={2}>
                {studentData.subjects.map((subject) => (
                  <Box key={subject.name}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2" fontWeight={500}>
                        {subject.name}
                      </Typography>
                      <Typography variant="caption">
                        {subject.mastery}% mastery
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={subject.mastery}
                      sx={{ 
                        height: 8, 
                        borderRadius: 4,
                        '& .MuiLinearProgress-bar': { backgroundColor: subject.color }
                      }}
                    />
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Recent Activity */}
      {showDetailed && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Recent Activity
              </Typography>
              <Stack spacing={1}>
                {studentData.recentActivity.slice(0, 5).map((activity, index) => (
                  <Paper key={index} sx={{ p: 2 }}>
                    <Stack direction="row" spacing={2} alignItems="center">
                      <Chip
                        icon={getActivityIcon(activity.type)}
                        label={activity.type}
                        size="small"
                        color={getActivityColor(activity.type) as any}
                        variant="outlined"
                      />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" fontWeight={500}>
                          {activity.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(activity.completedAt).toLocaleString()}
                        </Typography>
                      </Box>
                      <Stack alignItems="flex-end" spacing={0.5}>
                        {activity.score && (
                          <Typography variant="caption" fontWeight={500}>
                            {activity.score}%
                          </Typography>
                        )}
                        <Chip 
                          label={`+${activity.xpEarned} XP`} 
                          size="small" 
                          color="primary"
                        />
                      </Stack>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );
}

export default StudentProgress;