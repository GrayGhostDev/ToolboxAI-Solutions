import * as React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  Stack,
  Chip,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  IconButton,
  Button,
  Skeleton,
} from "@mui/material";
import {
  School,
  Person,
  TrendingUp,
  Assessment,
  EmojiEvents,
  SportsEsports,
  Refresh,
  Download,
  VerifiedUser,
  Warning,
} from "@mui/icons-material";
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
} from "recharts";
import { useAppDispatch, useAppSelector } from "../../../store";
import {
  fetchPlatformAnalytics,
  fetchPerformanceMetrics,
  fetchSubjectAnalytics,
  fetchComplianceMetrics,
  refreshAllAnalytics,
  setTimeRange,
  clearError,
} from "../../../store/slices/analyticsSlice";

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
  
  const handleTimeRangeChange = (newRange: string) => {
    dispatch(setTimeRange(newRange));
    dispatch(refreshAllAnalytics(newRange));
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
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="between">
          <Box>
            <Typography color="text.secondary" variant="overline">
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              backgroundColor: color + "15",
              borderRadius: 2,
              p: 1.5,
              display: "flex",
              alignItems: "center",
              color,
            }}
          >
            {icon}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );

  if (loading && !platform) {
    return (
      <Box sx={{ p: 3 }}>
        <Stack spacing={3}>
          <Skeleton variant="rectangular" height={60} />
          <Grid container spacing={3}>
            {[1, 2, 3, 4].map((i) => (
              <Grid item xs={12} sm={6} md={3} key={i}>
                <Skeleton variant="rectangular" height={140} />
              </Grid>
            ))}
          </Grid>
          <Skeleton variant="rectangular" height={400} />
        </Stack>
      </Box>
    );
  }
  
  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Platform Analytics
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => handleTimeRangeChange(e.target.value)}
            >
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
              <MenuItem value="1y">Last year</MenuItem>
            </Select>
          </FormControl>
          <IconButton onClick={handleRefresh} disabled={loading}>
            <Refresh />
          </IconButton>
          <Button variant="outlined" startIcon={<Download />} onClick={handleExport}>
            Export
          </Button>
        </Stack>
      </Stack>
      
      {error && (
        <Alert severity="error" onClose={() => dispatch(clearError())} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {lastUpdated && (
        <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
          Last updated: {new Date(lastUpdated).toLocaleString()}
        </Typography>
      )}

      {/* Overview Stats */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Users"
            value={platform?.totalUsers?.toLocaleString() || '0'}
            subtitle={platform?.growthRate ? `+${platform.growthRate}% growth` : 'Loading...'}
            icon={<Person />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Schools"
            value={platform?.totalSchools || 0}
            subtitle="Active institutions"
            icon={<School />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Lessons"
            value={platform?.totalLessons || 0}
            subtitle="Total available"
            icon={<Assessment />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Completion"
            value={`${platform?.averageCompletion || 0}%`}
            subtitle="Across all courses"
            icon={<TrendingUp />}
            color="#9c27b0"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Top Performers */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}>
                <EmojiEvents />
                Top Performers
              </Typography>
              {loading ? (
                <Stack spacing={2}>
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} variant="rectangular" height={60} />
                  ))}
                </Stack>
              ) : (
                <Stack spacing={2}>
                  {(performance?.topPerformers || []).slice(0, 5).map((performer, index) => (
                    <Paper key={performer.id} sx={{ p: 2 }}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Stack direction="row" alignItems="center" spacing={2}>
                          <Chip 
                            label={`#${index + 1}`} 
                            size="small" 
                            color={index === 0 ? "warning" : index < 3 ? "primary" : "default"}
                          />
                          <Typography fontWeight={500}>{performer.name}</Typography>
                        </Stack>
                        <Stack direction="row" spacing={1}>
                          <Chip label={`${performer.xp.toLocaleString()} XP`} size="small" />
                          <Chip label={`Lvl ${performer.level}`} size="small" color="primary" />
                          <Chip label={`${performer.badges} badges`} size="small" color="secondary" />
                        </Stack>
                      </Stack>
                    </Paper>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Subject Mastery */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}>
                <Assessment />
                Subject Mastery
              </Typography>
              {loading ? (
                <Stack spacing={2}>
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} variant="rectangular" height={60} />
                  ))}
                </Stack>
              ) : (
                <Stack spacing={2}>
                  {(subjects?.subjects || subjectMastery || []).map((subject: any, index: number) => (
                    <Box key={(subject as any).name || (subject as any).subject}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2" fontWeight={500}>
                          {(subject as any).name || (subject as any).subject}
                        </Typography>
                        <Typography variant="caption">
                          {(((subject as any).averageScore || (subject as any).mastery || 0) as number).toFixed(1)}%
                        </Typography>
                      </Stack>
                      <LinearProgress
                        variant="determinate"
                        value={(subject as any).completionRate || (subject as any).mastery || 0}
                        sx={{ 
                          height: 8, 
                          borderRadius: 4,
                          bgcolor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: (((subject as any).completionRate || (subject as any).mastery || 0) as number) >= 80 ? 'success.main' : 
                                    (((subject as any).completionRate || (subject as any).mastery || 0) as number) >= 60 ? 'warning.main' : 'error.main'
                          }
                        }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {(((subject as any).completionRate || (subject as any).mastery || 0) as number).toFixed(1)}% mastery
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Roblox Engagement */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}>
                <SportsEsports />
                Roblox Engagement Analytics
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h3" color="primary" fontWeight={700}>
                      {platform?.activeUsers?.toLocaleString() || '0'}
                    </Typography>
                    <Typography color="text.secondary">
                      Active Users Today
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h3" color="secondary" fontWeight={700}>
                      {platform?.averageEngagement || 0}%
                    </Typography>
                    <Typography color="text.secondary">
                      Engagement Rate
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" fontWeight={600} mb={1}>
                      Popular Worlds
                    </Typography>
                    <Stack spacing={1}>
                      {['Math Adventure', 'Science Lab', 'History Quest'].map((world, index) => (
                        <Chip
                          key={index}
                          label={world}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Stack>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}