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
} from "@mui/material";
import {
  School,
  Person,
  TrendingUp,
  Assessment,
  EmojiEvents,
  SportsEsports,
} from "@mui/icons-material";

interface AnalyticsData {
  totalUsers: number;
  totalSchools: number;
  totalLessons: number;
  totalAssessments: number;
  averageCompletion: number;
  topPerformers: Array<{
    name: string;
    xp: number;
    badges: number;
  }>;
  subjectMastery: Array<{
    subject: string;
    averageScore: number;
    completionRate: number;
  }>;
  robloxEngagement: {
    totalSessions: number;
    averageSessionTime: number;
    popularWorlds: string[];
  };
}

export default function Analytics() {
  const [timeRange, setTimeRange] = useState("30d");
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    totalUsers: 1234,
    totalSchools: 15,
    totalLessons: 156,
    totalAssessments: 89,
    averageCompletion: 78.5,
    topPerformers: [
      { name: "Alex Johnson", xp: 2450, badges: 12 },
      { name: "Sarah Williams", xp: 2380, badges: 11 },
      { name: "Mike Chen", xp: 2210, badges: 10 },
    ],
    subjectMastery: [
      { subject: "Mathematics", averageScore: 85.2, completionRate: 92.1 },
      { subject: "Science", averageScore: 78.6, completionRate: 88.4 },
      { subject: "Language Arts", averageScore: 82.3, completionRate: 89.7 },
      { subject: "History", averageScore: 76.9, completionRate: 85.2 },
    ],
    robloxEngagement: {
      totalSessions: 4567,
      averageSessionTime: 24.5,
      popularWorlds: ["Math Adventure", "Science Lab", "History Quest"],
    },
  });

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

  return (
    <Box>
      <Stack direction="row" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Platform Analytics
        </Typography>
        <FormControl sx={{ minWidth: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeRange}
            label="Time Range"
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <MenuItem value="7d">Last 7 days</MenuItem>
            <MenuItem value="30d">Last 30 days</MenuItem>
            <MenuItem value="90d">Last 90 days</MenuItem>
            <MenuItem value="1y">Last year</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {/* Overview Stats */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Users"
            value={analytics.totalUsers.toLocaleString()}
            subtitle="+12% from last month"
            icon={<Person />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Schools"
            value={analytics.totalSchools}
            subtitle="Active institutions"
            icon={<School />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Lessons"
            value={analytics.totalLessons}
            subtitle="Created this month"
            icon={<Assessment />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Completion"
            value={`${analytics.averageCompletion}%`}
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
              <Stack spacing={2}>
                {analytics.topPerformers.map((performer, index) => (
                  <Paper key={index} sx={{ p: 2 }}>
                    <Stack direction="row" justifyContent="between" alignItems="center">
                      <Stack direction="row" alignItems="center" spacing={2}>
                        <Chip label={`#${index + 1}`} size="small" color="primary" />
                        <Typography fontWeight={500}>{performer.name}</Typography>
                      </Stack>
                      <Stack direction="row" spacing={1}>
                        <Chip label={`${performer.xp} XP`} size="small" />
                        <Chip label={`${performer.badges} badges`} size="small" color="secondary" />
                      </Stack>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
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
              <Stack spacing={2}>
                {analytics.subjectMastery.map((subject, index) => (
                  <Box key={index}>
                    <Stack direction="row" justifyContent="between" alignItems="center" mb={1}>
                      <Typography variant="body2" fontWeight={500}>
                        {subject.subject}
                      </Typography>
                      <Typography variant="caption">
                        {subject.averageScore.toFixed(1)}% avg score
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={subject.completionRate}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {subject.completionRate.toFixed(1)}% completion rate
                    </Typography>
                  </Box>
                ))}
              </Stack>
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
                      {analytics.robloxEngagement.totalSessions.toLocaleString()}
                    </Typography>
                    <Typography color="text.secondary">
                      Total Game Sessions
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h3" color="secondary" fontWeight={700}>
                      {analytics.robloxEngagement.averageSessionTime}m
                    </Typography>
                    <Typography color="text.secondary">
                      Avg Session Duration
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" fontWeight={600} mb={1}>
                      Popular Worlds
                    </Typography>
                    <Stack spacing={1}>
                      {analytics.robloxEngagement.popularWorlds.map((world, index) => (
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