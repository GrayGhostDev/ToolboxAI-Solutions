/**
 * Example Dashboard Layouts
 *
 * Demonstrates various dashboard layouts using Mantine components.
 * Showcases best practices for responsive design and component composition.
 *
 * @module ExampleDashboardLayouts
 * @since 2025-10-01
 */

import { useState, memo } from 'react';
import {
  Container,
  Grid,
  Stack,
  Group,
  Title,
  Text,
  Card,
  Badge,
  Button,
  Select,
  Box,
  Paper,
  Tabs,
  Avatar,
  Progress,
} from '@mantine/core';
import {
  IconTrophy,
  IconChartBar,
  IconBook,
  IconUser,
  IconSettings,
} from '@tabler/icons-react';

// Roblox-themed components temporarily disabled for Vercel build
// import { Roblox3DButton } from '../components/roblox/Roblox3DButton';
// import { Roblox3DNavigation } from '../components/roblox/Roblox3DNavigation';
// import { Roblox3DMetricCard } from '../components/roblox/Roblox3DMetricCard';
// import { RobloxProgressBar } from '../components/roblox/RobloxProgressBar';
// import { RobloxAchievementBadge } from '../components/roblox/RobloxAchievementBadge';
// import { RobloxDashboardHeader } from '../components/roblox/RobloxDashboardHeader';

/**
 * Student Dashboard Layout
 *
 * A dashboard layout optimized for students showing progress, achievements, and tasks.
 */
export const StudentDashboardLayout = memo(() => {
  const navItems = [
    { id: 'home', label: 'Home', iconName: 'BOARD' },
    { id: 'courses', label: 'Courses', iconName: 'BOOKS' },
    { id: 'achievements', label: 'Achievements', iconName: 'TROPHY', badge: 3 },
    { id: 'profile', label: 'Profile', iconName: 'GRADUATION_CAP' },
  ];

  return (
    <Container fluid p="lg">
      {/* Navigation */}
      <Box mb="xl">
        <Tabs defaultValue="home">
          <Tabs.List>
            {navItems.map(item => (
              <Tabs.Tab
                key={item.id}
                value={item.id}
                leftSection={<IconBook />}
                onClick={() => console.log('Navigate to:', item.id)}
              >
                {item.label}
                {item.badge && <Badge ml="xs" size="xs" circle>{item.badge}</Badge>}
              </Tabs.Tab>
            ))}
          </Tabs.List>
        </Tabs>
      </Box>

      {/* Header with user info */}
      <Group align="center" gap="md" mb="xl">
        <Avatar size="lg">AS</Avatar>
        <Box>
          <Text size="lg" fw={600}>Welcome, Alex Student</Text>
          <Text size="sm" c="dimmed">Level 12 • 2450 / 3000 XP</Text>
        </Box>
      </Group>

      {/* Metrics Grid */}
      <Grid mt="xl" gutter="lg">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Total XP</Text>
            <Text size="xl" fw={700}>15,420</Text>
            <Badge color="green" size="sm" mt="xs">+12.5%</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Courses Completed</Text>
            <Text size="xl" fw={700}>8</Text>
            <Badge color="blue" size="sm" mt="xs">+2</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Achievements</Text>
            <Text size="xl" fw={700}>24</Text>
            <Badge color="yellow" size="sm" mt="xs">+5</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Streak Days</Text>
            <Text size="xl" fw={700}>15</Text>
            <Badge color="cyan" size="sm" mt="xs">+1</Badge>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Main Content Area */}
      <Grid mt="xl" gutter="lg">
        {/* Progress Section */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card shadow="md" padding="lg" radius="lg">
            <Title order={3} mb="md">Current Progress</Title>

            <Stack gap="lg">
              <Box>
                <Group justify="space-between" mb="xs">
                  <Text fw={600}>Python Fundamentals</Text>
                  <Badge color="green">75% Complete</Badge>
                </Group>
                <Progress value={75} size="lg" radius="md" />
              </Box>

              <Box>
                <Group justify="space-between" mb="xs">
                  <Text fw={600}>Web Development</Text>
                  <Badge color="blue">60% Complete</Badge>
                </Group>
                <Progress value={60} size="lg" radius="md" />
              </Box>

              <Box>
                <Group justify="space-between" mb="xs">
                  <Text fw={600}>Data Structures</Text>
                  <Badge color="orange">40% Complete</Badge>
                </Group>
                <Progress value={40} size="lg" radius="md" />
              </Box>
            </Stack>

            <Group mt="xl">
              <Button
                variant="filled"
                leftSection={<IconBook />}
                onClick={() => console.log('Continue learning')}
              >
                Continue Learning
              </Button>
              <Button
                variant="outline"
                leftSection={<IconBook />}
                onClick={() => console.log('View courses')}
              >
                View All Courses
              </Button>
            </Group>
          </Card>
        </Grid.Col>

        {/* Recent Achievements */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="md" padding="lg" radius="lg" h="100%">
            <Title order={3} mb="md">Recent Achievements</Title>

            <Stack gap="md">
              <Card withBorder padding="sm">
                <Group gap="xs" mb="xs">
                  <Badge color="violet" variant="filled">Rare</Badge>
                  <Text size="sm" fw={600}>Fast Learner</Text>
                </Group>
                <Text size="xs" c="dimmed">Complete 5 courses in one month</Text>
              </Card>
              <Card withBorder padding="sm">
                <Group gap="xs" mb="xs">
                  <Badge color="purple" variant="filled">Epic</Badge>
                  <Text size="sm" fw={600}>Perfect Score</Text>
                </Group>
                <Text size="xs" c="dimmed">Score 100% on 3 quizzes</Text>
              </Card>
              <Card withBorder padding="sm">
                <Group gap="xs" mb="xs">
                  <Badge color="orange" variant="filled">Legendary</Badge>
                  <Text size="sm" fw={600}>Code Master</Text>
                </Group>
                <Text size="xs" c="dimmed" mb="xs">Complete 50 coding challenges</Text>
                <Progress value={75} size="sm" radius="md" />
              </Card>
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  );
});

StudentDashboardLayout.displayName = 'StudentDashboardLayout';

/**
 * Teacher Dashboard Layout
 *
 * A dashboard for teachers with class management and student progress tracking.
 */
export const TeacherDashboardLayout = memo(() => {
  const navItems = [
    { id: 'overview', label: 'Overview', iconName: 'BOARD' },
    { id: 'classes', label: 'Classes', iconName: 'BOOKS', badge: 5 },
    { id: 'students', label: 'Students', iconName: 'GRADUATION_CAP' },
    { id: 'analytics', label: 'Analytics', iconName: 'LIGHT_BULB' },
  ];

  return (
    <Container fluid p="lg">
      {/* Navigation */}
      <Box mb="xl">
        <Tabs defaultValue="overview">
          <Tabs.List>
            {navItems.map(item => (
              <Tabs.Tab
                key={item.id}
                value={item.id}
                leftSection={<IconBook />}
                onClick={() => console.log('Navigate to:', item.id)}
              >
                {item.label}
                {item.badge && <Badge ml="xs" size="xs" circle>{item.badge}</Badge>}
              </Tabs.Tab>
            ))}
          </Tabs.List>
        </Tabs>
      </Box>

      {/* Header */}
      <Group justify="space-between" mb="xl">
        <Box>
          <Title order={2}>Teacher Dashboard</Title>
          <Text c="dimmed">Welcome back, Professor Smith</Text>
        </Box>
        <Group>
          <Button
            variant="filled"
            leftSection={<IconBook />}
            onClick={() => console.log('Create assignment')}
          >
            Create Assignment
          </Button>
          <Button
            variant="outline"
            leftSection={<IconChartBar />}
            onClick={() => console.log('View reports')}
          >
            View Reports
          </Button>
        </Group>
      </Group>

      {/* Class Overview Cards */}
      <Grid gutter="lg">
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Total Students</Text>
            <Text size="xl" fw={700}>156</Text>
            <Badge color="blue" size="sm" mt="xs">+8</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Active Classes</Text>
            <Text size="xl" fw={700}>5</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Avg. Performance</Text>
            <Text size="xl" fw={700}>87</Text>
            <Badge color="yellow" size="sm" mt="xs">+3.2%</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Pending Reviews</Text>
            <Text size="xl" fw={700}>12</Text>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Class List */}
      <Card mt="xl" shadow="md" padding="lg" radius="lg">
        <Title order={3} mb="md">Your Classes</Title>

        <Grid gutter="md">
          {['Python 101', 'Web Dev Advanced', 'Data Science', 'Machine Learning'].map((className, idx) => (
            <Grid.Col key={idx} span={{ base: 12, sm: 6, lg: 3 }}>
              <Paper p="md" radius="md" withBorder>
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Badge color="blue" variant="light">Active</Badge>
                    <Text size="sm" c="dimmed">{25 + idx * 5} students</Text>
                  </Group>
                  <Title order={4}>{className}</Title>
                  <Progress value={((idx + 1) * 200 / 1000) * 100} size="lg" radius="md" />
                  <Button
                    variant="filled"
                    size="sm"
                    fullWidth
                    leftSection={<IconBook />}
                    onClick={() => console.log(`View ${className}`)}
                  >
                    View Class
                  </Button>
                </Stack>
              </Paper>
            </Grid.Col>
          ))}
        </Grid>
      </Card>
    </Container>
  );
});

TeacherDashboardLayout.displayName = 'TeacherDashboardLayout';

/**
 * Admin Dashboard Layout
 *
 * Comprehensive admin dashboard with system metrics and controls.
 */
export const AdminDashboardLayout = memo(() => {
  const [selectedView, setSelectedView] = useState('overview');

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', iconName: 'BOARD' },
    { id: 'users', label: 'Users', iconName: 'GRADUATION_CAP', badge: 12 },
    { id: 'system', label: 'System', iconName: 'LIGHT_BULB' },
    { id: 'settings', label: 'Settings', iconName: 'TROPHY' },
  ];

  return (
    <Container fluid p="lg">
      {/* Top Navigation */}
      <Box mb="xl">
        <Tabs value={selectedView} onChange={(value) => setSelectedView(value || 'dashboard')}>
          <Tabs.List>
            {navItems.map(item => (
              <Tabs.Tab
                key={item.id}
                value={item.id}
                leftSection={<IconBook />}
              >
                {item.label}
                {item.badge && <Badge ml="xs" size="xs" circle>{item.badge}</Badge>}
              </Tabs.Tab>
            ))}
          </Tabs.List>
        </Tabs>
      </Box>

      {/* System Metrics */}
      <Grid gutter="lg" mb="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Total Users</Text>
            <Text size="xl" fw={700}>1,247</Text>
            <Badge color="blue" size="sm" mt="xs">+15.3%</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Active Sessions</Text>
            <Text size="xl" fw={700}>342</Text>
            <Badge color="green" size="sm" mt="xs">+8.1%</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Courses</Text>
            <Text size="xl" fw={700}>89</Text>
            <Badge color="cyan" size="sm" mt="xs">+2</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Achievements</Text>
            <Text size="xl" fw={700}>456</Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">System Load</Text>
            <Text size="xl" fw={700}>67%</Text>
            <Badge color="green" size="sm" mt="xs">-5.2%</Badge>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Card withBorder padding="md">
            <Text size="sm" c="dimmed" mb="xs">Uptime</Text>
            <Text size="xl" fw={700}>99.9%</Text>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Control Panel */}
      <Card shadow="md" padding="lg" radius="lg">
        <Title order={3} mb="md">System Controls</Title>

        <Grid gutter="md">
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Button
              variant="filled"
              fullWidth
              leftSection={<IconUser />}
              onClick={() => console.log('User management')}
            >
              User Management
            </Button>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Button
              variant="outline"
              fullWidth
              leftSection={<IconBook />}
              onClick={() => console.log('Content management')}
            >
              Content Management
            </Button>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Button
              variant="filled"
              fullWidth
              leftSection={<IconChartBar />}
              onClick={() => console.log('Analytics')}
            >
              Analytics
            </Button>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Button
              variant="filled"
              fullWidth
              leftSection={<IconTrophy />}
              onClick={() => console.log('Gamification')}
            >
              Gamification
            </Button>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Button
              variant="filled"
              fullWidth
              leftSection={<IconSettings />}
              onClick={() => console.log('System settings')}
            >
              System Settings
            </Button>
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Button
              variant="filled"
              fullWidth
              leftSection={<IconChartBar />}
              onClick={() => console.log('Reports')}
            >
              Reports
            </Button>
          </Grid.Col>
        </Grid>
      </Card>
    </Container>
  );
});

AdminDashboardLayout.displayName = 'AdminDashboardLayout';

/**
 * Main component showcasing all layouts
 */
export const ExampleDashboardLayouts = memo(() => {
  const [selectedLayout, setSelectedLayout] = useState<string>('student');

  return (
    <Box>
      <Container size="xl" py="xl">
        <Stack gap="lg">
          <Box>
            <Title order={1}>Example Dashboard Layouts</Title>
            <Text c="dimmed" size="lg" mt="xs">
              Explore different dashboard layouts built with Mantine components
            </Text>
          </Box>

          <Select
            label="Select Layout"
            placeholder="Choose a layout to view"
            value={selectedLayout}
            onChange={(value) => setSelectedLayout(value || 'student')}
            data={[
              { value: 'student', label: 'Student Dashboard' },
              { value: 'teacher', label: 'Teacher Dashboard' },
              { value: 'admin', label: 'Admin Dashboard' },
            ]}
            size="lg"
            w={300}
          />
        </Stack>
      </Container>

      <Box mt="xl">
        {selectedLayout === 'student' && <StudentDashboardLayout />}
        {selectedLayout === 'teacher' && <TeacherDashboardLayout />}
        {selectedLayout === 'admin' && <AdminDashboardLayout />}
      </Box>
    </Box>
  );
});

ExampleDashboardLayouts.displayName = 'ExampleDashboardLayouts';

export default ExampleDashboardLayouts;
