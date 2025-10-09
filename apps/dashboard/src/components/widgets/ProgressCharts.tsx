import React, { useEffect, useState } from 'react';
import { Card, Grid, Text, Box } from '@mantine/core';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  RadialBarChart,
  RadialBar,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { type UserRole } from '../../types';
import { useMantineTheme } from '@mantine/core';
import { usePusherContext } from '../PusherProvider';
import { pusherClient } from '../../services/pusher-client';
export function ProgressCharts({ role }: { role: UserRole }) {
  const theme = useMantineTheme();
  const { isConnected } = usePusherContext();

  // Real-time chart data states
  const [weeklyData, setWeeklyData] = useState([
    { day: 'Mon', xp: 120, hours: 2.5 },
    { day: 'Tue', xp: 180, hours: 3.2 },
    { day: 'Wed', xp: 140, hours: 2.8 },
    { day: 'Thu', xp: 220, hours: 4.1 },
    { day: 'Fri', xp: 190, hours: 3.5 },
    { day: 'Sat', xp: 60, hours: 1.2 },
    { day: 'Sun', xp: 40, hours: 0.8 },
  ]);

  const [subjectData, setSubjectData] = useState([
    { subject: 'Math', mastery: 78, avgScore: 85 },
    { subject: 'Science', mastery: 64, avgScore: 72 },
    { subject: 'Language', mastery: 82, avgScore: 88 },
    { subject: 'Arts', mastery: 70, avgScore: 75 },
    { subject: 'Tech', mastery: 90, avgScore: 92 },
  ]);

  const [levelData, setLevelData] = useState([{ name: 'Level Progress', value: 65, fill: theme.colors.blue[6] }]);

  const [skillsData, setSkillsData] = useState([
    { skill: 'Problem Solving', A: 85, fullMark: 100 },
    { skill: 'Critical Thinking', A: 78, fullMark: 100 },
    { skill: 'Creativity', A: 92, fullMark: 100 },
    { skill: 'Collaboration', A: 70, fullMark: 100 },
    { skill: 'Communication', A: 88, fullMark: 100 },
    { skill: 'Digital Literacy', A: 95, fullMark: 100 },
  ]);

  const [activityData, setActivityData] = useState([
    { name: 'Lessons', value: 35, color: theme.colors.blue[6] },
    { name: 'Quizzes', value: 25, color: theme.colors.green[6] },
    { name: 'Projects', value: 20, color: theme.colors.yellow[6] },
    { name: 'Games', value: 20, color: theme.colors.violet[6] },
  ]);

  // Subscribe to Pusher for real-time chart updates
  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to dashboard-updates channel for chart data
    const dashboardChannel = pusherClient.subscribe('dashboard-updates');

    if (dashboardChannel) {
      // Bind to weekly data updates
      pusherClient.bind('dashboard-updates', 'weekly-data-update', (data: any) => {
        console.log('Weekly chart data updated:', data);
        setWeeklyData(data.weeklyData);
      });

      // Bind to subject data updates
      pusherClient.bind('dashboard-updates', 'subject-data-update', (data: any) => {
        console.log('Subject chart data updated:', data);
        setSubjectData(data.subjectData);
      });

      // Bind to progress level updates
      pusherClient.bind('dashboard-updates', 'level-progress-update', (data: any) => {
        console.log('Level progress updated:', data);
        setLevelData([{ ...levelData[0], value: data.progress }]);
      });

      // Bind to skills data updates
      pusherClient.bind('dashboard-updates', 'skills-data-update', (data: any) => {
        console.log('Skills data updated:', data);
        setSkillsData(data.skillsData);
      });

      // Bind to activity distribution updates
      pusherClient.bind('dashboard-updates', 'activity-data-update', (data: any) => {
        console.log('Activity data updated:', data);
        setActivityData(data.activityData);
      });
    }

    // Cleanup function
    return () => {
      if (dashboardChannel) {
        pusherClient.unbind('dashboard-updates', 'weekly-data-update');
        pusherClient.unbind('dashboard-updates', 'subject-data-update');
        pusherClient.unbind('dashboard-updates', 'level-progress-update');
        pusherClient.unbind('dashboard-updates', 'skills-data-update');
        pusherClient.unbind('dashboard-updates', 'activity-data-update');
        pusherClient.unsubscribe('dashboard-updates');
      }
    };
  }, [isConnected]);

  const chartColors = {
    primary: theme.colors.blue[6],
    secondary: theme.colors.cyan[6],
    warning: theme.colors.yellow[6],
    info: theme.colors.indigo[6],
    success: theme.colors.green[6],
  };

  return (
    <Grid>
      {/* Weekly XP Progress */}
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card shadow="sm" p="md" role="region" aria-label="Weekly XP chart">
          <Text size="lg" fw={600} mb="md">
            Weekly {role === 'student' ? 'XP Progress' : 'Class Activity'}
          </Text>
          <Box h={300}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.gray[3]} />
                <XAxis dataKey="day" stroke={theme.colors.gray[6]} />
                <YAxis stroke={theme.colors.gray[6]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme.colors.gray[0],
                    border: `1px solid ${theme.colors.gray[3]}`,
                    borderRadius: 8,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="xp"
                  stroke={chartColors.primary}
                  strokeWidth={3}
                  dot={{ fill: chartColors.primary, r: 4 }}
                  activeDot={{ r: 6 }}
                />
                {role === 'teacher' && (
                  <Line
                    type="monotone"
                    dataKey="hours"
                    stroke={chartColors.secondary}
                    strokeWidth={3}
                    dot={{ fill: chartColors.secondary, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </Card>
      </Grid.Col>
      {/* Subject Mastery */}
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card shadow="sm" p="md" role="region" aria-label="Subject mastery bar chart">
          <Text size="lg" fw={600} mb="md">
            Subject {role === 'student' ? 'Mastery' : 'Performance'}
          </Text>
          <Box h={300}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={subjectData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.gray[3]} />
                <XAxis dataKey="subject" stroke={theme.colors.gray[6]} />
                <YAxis stroke={theme.colors.gray[6]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme.colors.gray[0],
                    border: `1px solid ${theme.colors.gray[3]}`,
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="mastery" fill={chartColors.primary} radius={[8, 8, 0, 0]} />
                {role === 'teacher' && (
                  <Bar dataKey="avgScore" fill={chartColors.secondary} radius={[8, 8, 0, 0]} />
                )}
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Card>
      </Grid.Col>
      {/* Skills Radar Chart */}
      {role === 'student' && (
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card shadow="sm" p="md" role="region" aria-label="Skills radar chart">
            <Text size="lg" fw={600} mb="md">
              Skill Development
            </Text>
            <Box h={300}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={skillsData}>
                  <PolarGrid stroke={theme.colors.gray[3]} />
                  <PolarAngleAxis dataKey="skill" stroke={theme.colors.gray[6]} />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    stroke={theme.colors.gray[6]}
                  />
                  <Radar
                    name="Skills"
                    dataKey="A"
                    stroke={chartColors.primary}
                    fill={chartColors.primary}
                    fillOpacity={0.6}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.colors.gray[0],
                      border: `1px solid ${theme.colors.gray[3]}`,
                      borderRadius: 8,
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </Box>
          </Card>
        </Grid.Col>
      )}
      {/* Activity Distribution */}
      <Grid.Col span={{ base: 12, md: role === 'student' ? 6 : 4 }}>
        <Card shadow="sm" p="md" role="region" aria-label="Activity distribution pie chart">
          <Text size="lg" fw={600} mb="md">
            Activity Distribution
          </Text>
          <Box h={300}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={activityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {activityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme.colors.gray[0],
                    border: `1px solid ${theme.colors.gray[3]}`,
                    borderRadius: 8,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </Box>
        </Card>
      </Grid.Col>
      {/* Level Progress (for Students) or Completion Rate (for others) */}
      {role !== 'parent' && (
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="sm" p="md" role="region" aria-label="Progress radial chart">
            <Text size="lg" fw={600} mb="md">
              {role === 'student' ? 'Level Progress' : 'Completion Rate'}
            </Text>
            <Box h={300}>
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius="60%"
                  outerRadius="90%"
                  barSize={10}
                  data={levelData}
                  startAngle={90}
                  endAngle={-270}
                >
                  <RadialBar
                    background
                    dataKey="value"
                    cornerRadius={12}
                    fill={chartColors.primary}
                  />
                  <Legend
                    iconSize={10}
                    layout="horizontal"
                    verticalAlign="bottom"
                    align="center"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.colors.gray[0],
                      border: `1px solid ${theme.colors.gray[3]}`,
                      borderRadius: 8,
                    }}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
            </Box>
          </Card>
        </Grid.Col>
      )}
      {/* Monthly Trend (for Teachers and Admins) */}
      {(role === 'teacher' || role === 'admin') && (
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="sm" p="md" role="region" aria-label="Monthly trend">
            <Text size="lg" fw={600} mb="md">
              Monthly Trend
            </Text>
            <Box h={300}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={[
                    { month: 'Jan', students: 82 },
                    { month: 'Feb', students: 85 },
                    { month: 'Mar', students: 88 },
                    { month: 'Apr', students: 86 },
                    { month: 'May', students: 90 },
                  ]}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.gray[3]} />
                  <XAxis dataKey="month" stroke={theme.colors.gray[6]} />
                  <YAxis stroke={theme.colors.gray[6]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.colors.gray[0],
                      border: `1px solid ${theme.colors.gray[3]}`,
                      borderRadius: 8,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="students"
                    stroke={chartColors.success}
                    strokeWidth={3}
                    dot={{ fill: chartColors.success, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Card>
        </Grid.Col>
      )}
    </Grid>
  );
}