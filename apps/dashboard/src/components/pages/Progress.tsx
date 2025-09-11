import React, { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  LinearProgress,
  Chip,
  Avatar,
  Button,
  IconButton,
  Tab,
  Tabs,
  Paper,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Badge,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import {
  TrendingUp,
  TrendingDown,
  EmojiEvents,
  School,
  Timer,
  CheckCircle,
  RadioButtonUnchecked,
  Star,
  LocalFireDepartment,
  Psychology,
  CalendarToday,
  Refresh,
  Download,
  Compare,
  Assessment,
} from "@mui/icons-material";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from "recharts";
import { useAppDispatch, useAppSelector } from "../../store";
import {
  fetchStudentProgress,
  fetchClassProgress,
  fetchLessonAnalytics,
  setFilters,
  setCurrentStudent,
  compareStudents,
  generateProgressReport,
  clearError,
} from "../../store/slices/progressSlice";

const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff7c7c", "#8dd1e1"];

export default function Progress() {
  const dispatch = useAppDispatch();
  const {
    studentProgress,
    classProgress,
    lessonAnalytics,
    currentStudentId,
    currentClassId,
    loading,
    error,
    filters,
    comparisons,
  } = useAppSelector((state) => state.progress);
  
  const user = useAppSelector((state) => state.user);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedSubject, setSelectedSubject] = useState<string>("all");
  const [timeRange, setTimeRange] = useState(30);
  
  // Fetch progress data on mount
  useEffect(() => {
    if (user.role === "student" && user.id) {
      dispatch(fetchStudentProgress({ studentId: user.id, daysBack: timeRange }));
    } else if (user.role === "teacher" && user.classIds?.[0]) {
      dispatch(fetchClassProgress({ classId: user.classIds[0], daysBack: timeRange }));
    }
  }, [dispatch, user, timeRange]);
  
  const currentProgress = currentStudentId ? studentProgress[currentStudentId] : null;
  const currentClass = currentClassId ? classProgress[currentClassId] : null;
  
  const handleRefresh = () => {
    if (currentStudentId) {
      dispatch(fetchStudentProgress({ studentId: currentStudentId, daysBack: timeRange }));
    }
    if (currentClassId) {
      dispatch(fetchClassProgress({ classId: currentClassId, daysBack: timeRange }));
    }
  };
  
  const handleExportReport = () => {
    if (currentStudentId) {
      dispatch(generateProgressReport({ studentId: currentStudentId, format: "pdf" }));
    }
  };
  
  const handleCompareStudents = (studentIds: string[]) => {
    dispatch(compareStudents(studentIds));
  };
  
  // Mock data for demonstration (will be replaced with real data from API)
  const mockXPData = [
    { date: "Mon", xp: 150 },
    { date: "Tue", xp: 230 },
    { date: "Wed", xp: 180 },
    { date: "Thu", xp: 290 },
    { date: "Fri", xp: 310 },
    { date: "Sat", xp: 250 },
    { date: "Sun", xp: 380 },
  ];
  
  const mockSubjectData = [
    { subject: "Math", mastery: 85, hours: 12 },
    { subject: "Science", mastery: 72, hours: 10 },
    { subject: "Language", mastery: 90, hours: 15 },
    { subject: "History", mastery: 68, hours: 8 },
    { subject: "Arts", mastery: 95, hours: 6 },
  ];
  
  const mockSkillData = [
    { skill: "Problem Solving", level: 85 },
    { skill: "Critical Thinking", level: 78 },
    { skill: "Creativity", level: 92 },
    { skill: "Collaboration", level: 88 },
    { skill: "Communication", level: 75 },
    { skill: "Digital Literacy", level: 95 },
  ];
  
  const mockBadges = [
    { id: "1", name: "Math Wizard", icon: "🧙", rarity: "epic", earned: true },
    { id: "2", name: "Speed Reader", icon: "📚", rarity: "rare", earned: true },
    { id: "3", name: "Science Explorer", icon: "🔬", rarity: "common", earned: true },
    { id: "4", name: "Perfect Week", icon: "⭐", rarity: "legendary", earned: false },
    { id: "5", name: "Team Player", icon: "🤝", rarity: "rare", earned: true },
    { id: "6", name: "Early Bird", icon: "🌅", rarity: "common", earned: true },
  ];
  
  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case "legendary": return "#FFD700";
      case "epic": return "#9B30FF";
      case "rare": return "#0099FF";
      default: return "#888888";
    }
  };
  
  if (loading && !currentProgress && !currentClass) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Grid2 container spacing={3}>
      {/* Header */}
      <Grid2 size={12}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Learning Progress
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Time Range</InputLabel>
                  <Select
                    value={timeRange}
                    label="Time Range"
                    onChange={(e) => setTimeRange(e.target.value as number)}
                  >
                    <MenuItem value={7}>Last Week</MenuItem>
                    <MenuItem value={30}>Last Month</MenuItem>
                    <MenuItem value={90}>Last 3 Months</MenuItem>
                    <MenuItem value={365}>Last Year</MenuItem>
                  </Select>
                </FormControl>
                <IconButton onClick={handleRefresh} disabled={loading}>
                  <Refresh />
                </IconButton>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={handleExportReport}
                >
                  Export Report
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>
      
      {error && (
        <Grid2 size={12}>
          <Alert severity="error" onClose={() => dispatch(clearError())}>
            {error}
          </Alert>
        </Grid2>
      )}
      
      {/* Key Metrics */}
      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <LocalFireDepartment color="error" />
                <Typography variant="caption" color="text.secondary">
                  Current Streak
                </Typography>
              </Stack>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                7 Days
              </Typography>
              <Chip label="Personal Best!" color="success" size="small" />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>
      
      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <EmojiEvents color="warning" />
                <Typography variant="caption" color="text.secondary">
                  Total XP
                </Typography>
              </Stack>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                2,450
              </Typography>
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <TrendingUp color="success" fontSize="small" />
                <Typography variant="caption" color="success.main">
                  +320 this week
                </Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>
      
      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <School color="primary" />
                <Typography variant="caption" color="text.secondary">
                  Lessons Completed
                </Typography>
              </Stack>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                42/50
              </Typography>
              <LinearProgress variant="determinate" value={84} color="primary" />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>
      
      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={2}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Psychology color="secondary" />
                <Typography variant="caption" color="text.secondary">
                  Skill Level
                </Typography>
              </Stack>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                Level 12
              </Typography>
              <Typography variant="caption" color="text.secondary">
                450 XP to Level 13
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>
      
      {/* Charts Section */}
      <Grid2 size={12}>
        <Card>
          <CardContent>
            <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 3 }}>
              <Tab label="XP Progress" />
              <Tab label="Subject Mastery" />
              <Tab label="Skills Radar" />
              <Tab label="Achievements" />
            </Tabs>
            
            {/* XP Progress Chart */}
            {activeTab === 0 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Weekly XP Progress
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={mockXPData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <ChartTooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="xp"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={{ fill: "#8884d8" }}
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            )}
            
            {/* Subject Mastery Chart */}
            {activeTab === 1 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Subject Mastery & Time Spent
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={mockSubjectData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="subject" />
                    <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                    <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                    <ChartTooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="mastery" fill="#8884d8" name="Mastery %" />
                    <Bar yAxisId="right" dataKey="hours" fill="#82ca9d" name="Hours" />
                  </BarChart>
                </ResponsiveContainer>
                
                <Grid2 container spacing={2} sx={{ mt: 3 }}>
                  {mockSubjectData.map((subject) => (
                    <Grid2 key={subject.subject} size={{ xs: 12, sm: 6, md: 2.4 }}>
                      <Paper sx={{ p: 2, textAlign: "center" }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {subject.subject}
                        </Typography>
                        <Box position="relative" display="inline-flex">
                          <CircularProgress
                            variant="determinate"
                            value={subject.mastery}
                            size={60}
                            thickness={5}
                            color={subject.mastery >= 80 ? "success" : subject.mastery >= 60 ? "warning" : "error"}
                          />
                          <Box
                            top={0}
                            left={0}
                            bottom={0}
                            right={0}
                            position="absolute"
                            display="flex"
                            alignItems="center"
                            justifyContent="center"
                          >
                            <Typography variant="caption" component="div" color="text.secondary">
                              {`${subject.mastery}%`}
                            </Typography>
                          </Box>
                        </Box>
                      </Paper>
                    </Grid2>
                  ))}
                </Grid2>
              </Box>
            )}
            
            {/* Skills Radar Chart */}
            {activeTab === 2 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Skills Development
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={mockSkillData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="skill" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Skill Level"
                      dataKey="level"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </Box>
            )}
            
            {/* Achievements */}
            {activeTab === 3 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Badges & Achievements
                </Typography>
                <Grid2 container spacing={2}>
                  {mockBadges.map((badge) => (
                    <Grid2 key={badge.id} size={{ xs: 6, sm: 4, md: 2 }}>
                      <Paper
                        sx={{
                          p: 2,
                          textAlign: "center",
                          opacity: badge.earned ? 1 : 0.5,
                          border: `2px solid ${badge.earned ? getRarityColor(badge.rarity) : '#ddd'}`,
                          position: "relative",
                        }}
                      >
                        {badge.earned && (
                          <CheckCircle
                            sx={{
                              position: "absolute",
                              top: 8,
                              right: 8,
                              color: "success.main",
                              fontSize: 20,
                            }}
                          />
                        )}
                        <Typography variant="h2" sx={{ mb: 1 }}>
                          {badge.icon}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {badge.name}
                        </Typography>
                        <Chip
                          label={badge.rarity}
                          size="small"
                          sx={{
                            mt: 1,
                            bgcolor: getRarityColor(badge.rarity),
                            color: "white",
                          }}
                        />
                      </Paper>
                    </Grid2>
                  ))}
                </Grid2>
                
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Earned: {mockBadges.filter(b => b.earned).length} / {mockBadges.length}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(mockBadges.filter(b => b.earned).length / mockBadges.length) * 100}
                    sx={{ width: 200 }}
                  />
                </Stack>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid2>
      
      {/* Recent Activity */}
      <Grid2 size={{ xs: 12, md: 6 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Recent Achievements
            </Typography>
            <List>
              {[
                { title: "Completed Math Chapter 5", xp: 150, time: "2 hours ago", icon: "📐" },
                { title: "Perfect Score on Science Quiz", xp: 200, time: "Yesterday", icon: "🔬" },
                { title: "7-Day Streak Achieved", xp: 100, time: "2 days ago", icon: "🔥" },
                { title: "Helped 3 Classmates", xp: 75, time: "3 days ago", icon: "🤝" },
              ].map((activity, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: "primary.light" }}>
                        {activity.icon}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={activity.title}
                      secondary={activity.time}
                    />
                    <Chip
                      label={`+${activity.xp} XP`}
                      color="success"
                      size="small"
                    />
                  </ListItem>
                  {index < 3 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid2>
      
      {/* Improvement Suggestions */}
      <Grid2 size={{ xs: 12, md: 6 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Recommended Focus Areas
            </Typography>
            <Stack spacing={2}>
              {[
                {
                  subject: "History",
                  reason: "Below average performance",
                  action: "Review Chapter 3-4",
                  improvement: "+15%",
                },
                {
                  subject: "Science",
                  reason: "Upcoming test",
                  action: "Practice lab exercises",
                  improvement: "+10%",
                },
                {
                  subject: "Math",
                  reason: "Strong foundation",
                  action: "Try advanced problems",
                  improvement: "Challenge",
                },
              ].map((suggestion, index) => (
                <Paper key={index} sx={{ p: 2 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {suggestion.subject}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {suggestion.reason}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {suggestion.action}
                      </Typography>
                    </Box>
                    <Chip
                      label={suggestion.improvement}
                      color={suggestion.improvement === "Challenge" ? "primary" : "success"}
                      variant="outlined"
                    />
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid2>
    </Grid2>
  );
}