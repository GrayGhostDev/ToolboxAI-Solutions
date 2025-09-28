import React, { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Paper,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  School,
  People,
  Assignment,
  CheckCircle,
  Schedule,
  EmojiEvents,
} from '@mui/icons-material';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
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
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import useRealTimeData from '../../hooks/useRealTimeData';

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

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, color }) => {
  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="caption">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            {change !== undefined && (
              <Box display="flex" alignItems="center" mt={1}>
                {change >= 0 ? (
                  <TrendingUp color="success" fontSize="small" />
                ) : (
                  <TrendingDown color="error" fontSize="small" />
                )}
                <Typography
                  variant="body2"
                  color={change >= 0 ? 'success.main' : 'error.main'}
                  ml={0.5}
                >
                  {Math.abs(change)}%
                </Typography>
              </Box>
            )}
          </Box>
          <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
};

const RealTimeAnalytics: React.FC = () => {
  const { isConnected } = useWebSocketContext();
  const { data: analyticsData, loading } = useRealTimeData<any>('analytics', {
    refreshInterval: 5000,
  });

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

  const [recentActivities] = useState([
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

  // Update metrics when analytics data changes
  useEffect(() => {
    if (analyticsData) {
      setMetrics({
        activeUsers: analyticsData.activeUsers || Math.floor(Math.random() * 100) + 150,
        completedLessons: analyticsData.completedLessons || Math.floor(Math.random() * 50) + 200,
        averageScore: analyticsData.averageScore || Math.floor(Math.random() * 20) + 75,
        engagementRate: analyticsData.engagementRate || Math.floor(Math.random() * 30) + 65,
      });

      // Update charts if new data available
      if (analyticsData.activityChart) {
        setActivityData(analyticsData.activityChart);
      }
      if (analyticsData.performanceChart) {
        setPerformanceData(analyticsData.performanceChart);
      }
    }
  }, [analyticsData]);

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
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Real-Time Analytics Dashboard
      </Typography>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Connection Status */}
      <Box sx={{ mb: 2 }}>
        <Chip
          label={isConnected ? 'Live Data' : 'Offline'}
          color={isConnected ? 'success' : 'error'}
          size="small"
          sx={{ mr: 1 }}
        />
        {isConnected && (
          <Chip
            label="Auto-refresh: 5s"
            color="primary"
            variant="outlined"
            size="small"
          />
        )}
      </Box>

      {/* Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Users"
            value={metrics.activeUsers}
            change={12}
            icon={<People />}
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Completed Lessons"
            value={metrics.completedLessons}
            change={8}
            icon={<CheckCircle />}
            color="#2196f3"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Average Score"
            value={`${metrics.averageScore}%`}
            change={-2}
            icon={<School />}
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Engagement Rate"
            value={`${metrics.engagementRate}%`}
            change={15}
            icon={<EmojiEvents />}
            color="#9c27b0"
          />
        </Grid>
      </Grid>

      {/* Assignment Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Assignment color="primary" />
              <Typography variant="h6">Assignment Analytics</Typography>
            </Box>
            <Box sx={{ height: 200 }}>
              <Bar
                data={{
                  labels: ['Math', 'Science', 'English', 'History', 'Art'],
                  datasets: [
                    {
                      label: 'Completed',
                      data: [85, 78, 92, 68, 74],
                      backgroundColor: 'rgba(54, 162, 235, 0.6)',
                      borderColor: 'rgba(54, 162, 235, 1)',
                      borderWidth: 1,
                    },
                    {
                      label: 'Pending',
                      data: [15, 22, 8, 32, 26],
                      backgroundColor: 'rgba(255, 99, 132, 0.6)',
                      borderColor: 'rgba(255, 99, 132, 1)',
                      borderWidth: 1,
                    }
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'top' as const,
                    },
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                    },
                  },
                }}
              />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Recent Activity Summary</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Avatar sx={{ bgcolor: 'success.main' }}>
                <CheckCircle />
              </Avatar>
              <Box>
                <Typography variant="body1">24 assignments completed today</Typography>
                <Typography variant="body2" color="text.secondary">
                  15% increase from yesterday
                </Typography>
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: 'warning.main' }}>
                <Schedule />
              </Avatar>
              <Box>
                <Typography variant="body1">12 assignments due this week</Typography>
                <Typography variant="body2" color="text.secondary">
                  Across 5 different subjects
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="Weekly Activity Trend" />
            <CardContent>
              <Box sx={{ height: 300 }}>
                <Line data={activityData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Subject Performance" />
            <CardContent>
              <Box sx={{ height: 300 }}>
                <Doughnut data={performanceData} options={doughnutOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activities */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Recent Student Activities" />
            <CardContent>
              <List>
                {recentActivities.map((activity, index) => (
                  <React.Fragment key={activity.id}>
                    <ListItem>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: '#2196f3' }}>
                          {activity.user[0]}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={activity.user}
                        secondary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body2" component="span">
                              {activity.action}
                            </Typography>
                            {activity.score && (
                              <Chip
                                label={`${activity.score}%`}
                                size="small"
                                color={activity.score >= 80 ? 'success' : 'warning'}
                              />
                            )}
                          </Box>
                        }
                      />
                      <Typography variant="caption" color="textSecondary">
                        <Schedule fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                        {activity.time}
                      </Typography>
                    </ListItem>
                    {index < recentActivities.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default RealTimeAnalytics;
