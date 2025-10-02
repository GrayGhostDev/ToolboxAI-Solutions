/**
 * Example Dashboard Layouts
 *
 * Demonstrates various dashboard layouts using Roblox components.
 * Showcases best practices for responsive design and component composition.
 *
 * @module ExampleDashboardLayouts
 * @since 2025-10-01
 */

import React, { useState, memo } from 'react';
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
} from '@mantine/core';
import {
  IconTrophy,
  IconChartBar,
  IconBook,
  IconUser,
  IconSettings,
  IconBell,
} from '@tabler/icons-react';

// Import Roblox components
import { Roblox3DButton } from '../components/roblox/Roblox3DButton';
import { Roblox3DNavigation } from '../components/roblox/Roblox3DNavigation';
import { Roblox3DMetricCard } from '../components/roblox/Roblox3DMetricCard';
import { RobloxProgressBar } from '../components/roblox/RobloxProgressBar';
import { RobloxAchievementBadge } from '../components/roblox/RobloxAchievementBadge';
import { RobloxDashboardHeader } from '../components/roblox/RobloxDashboardHeader';

/**
 * Student Dashboard Layout
 *
 * A dashboard layout optimized for students showing progress, achievements, and tasks.
 */
export const StudentDashboardLayout = memo(() => {
  const [activeTab, setActiveTab] = useState('overview');

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
        <Roblox3DNavigation
          items={navItems}
          onItemClick={(item) => console.log('Navigate to:', item.id)}
          variant="buttons"
          orientation="horizontal"
          animated={true}
        />
      </Box>

      {/* Header with user info */}
      <RobloxDashboardHeader
        userName="Alex Student"
        level={12}
        xp={2450}
        maxXp={3000}
        avatarUrl="/avatars/student.png"
      />

      {/* Metrics Grid */}
      <Grid mt="xl" gutter="lg">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Roblox3DMetricCard
            title="Total XP"
            value={15420}
            change={+12.5}
            iconName="LIGHT_BULB"
            variant="success"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Roblox3DMetricCard
            title="Courses Completed"
            value={8}
            change={+2}
            iconName="BOOKS"
            variant="primary"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Roblox3DMetricCard
            title="Achievements"
            value={24}
            change={+5}
            iconName="TROPHY"
            variant="warning"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Roblox3DMetricCard
            title="Streak Days"
            value={15}
            change={+1}
            iconName="GRADUATION_CAP"
            variant="info"
            animated={true}
          />
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
                <RobloxProgressBar
                  currentXP={750}
                  requiredXP={1000}
                  level={5}
                  showLevel={false}
                  animated={true}
                  variant="gradient"
                />
              </Box>

              <Box>
                <Group justify="space-between" mb="xs">
                  <Text fw={600}>Web Development</Text>
                  <Badge color="blue">60% Complete</Badge>
                </Group>
                <RobloxProgressBar
                  currentXP={600}
                  requiredXP={1000}
                  level={4}
                  showLevel={false}
                  animated={true}
                  variant="gradient"
                />
              </Box>

              <Box>
                <Group justify="space-between" mb="xs">
                  <Text fw={600}>Data Structures</Text>
                  <Badge color="orange">40% Complete</Badge>
                </Group>
                <RobloxProgressBar
                  currentXP={400}
                  requiredXP={1000}
                  level={3}
                  showLevel={false}
                  animated={true}
                  variant="gradient"
                />
              </Box>
            </Stack>

            <Group mt="xl">
              <Roblox3DButton
                iconName="BOOKS"
                label="Continue Learning"
                variant="primary"
                size="medium"
                onClick={() => console.log('Continue learning')}
              />
              <Roblox3DButton
                iconName="BOARD"
                label="View All Courses"
                variant="secondary"
                size="medium"
                onClick={() => console.log('View courses')}
              />
            </Group>
          </Card>
        </Grid.Col>

        {/* Recent Achievements */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="md" padding="lg" radius="lg" h="100%">
            <Title order={3} mb="md">Recent Achievements</Title>

            <Stack gap="md">
              <RobloxAchievementBadge
                title="Fast Learner"
                description="Complete 5 courses in one month"
                iconName="LIGHT_BULB"
                rarity="rare"
                unlocked={true}
              />
              <RobloxAchievementBadge
                title="Perfect Score"
                description="Score 100% on 3 quizzes"
                iconName="TROPHY"
                rarity="epic"
                unlocked={true}
              />
              <RobloxAchievementBadge
                title="Code Master"
                description="Complete 50 coding challenges"
                iconName="GRADUATION_CAP"
                rarity="legendary"
                unlocked={false}
                progress={75}
              />
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
        <Roblox3DNavigation
          items={navItems}
          onItemClick={(item) => console.log('Navigate to:', item.id)}
          variant="tabs"
          orientation="horizontal"
          animated={true}
        />
      </Box>

      {/* Header */}
      <Group justify="space-between" mb="xl">
        <Box>
          <Title order={2}>Teacher Dashboard</Title>
          <Text c="dimmed">Welcome back, Professor Smith</Text>
        </Box>
        <Group>
          <Roblox3DButton
            iconName="BOARD"
            label="Create Assignment"
            variant="primary"
            onClick={() => console.log('Create assignment')}
          />
          <Roblox3DButton
            iconName="LIGHT_BULB"
            label="View Reports"
            variant="secondary"
            onClick={() => console.log('View reports')}
          />
        </Group>
      </Group>

      {/* Class Overview Cards */}
      <Grid gutter="lg">
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Roblox3DMetricCard
            title="Total Students"
            value={156}
            change={+8}
            iconName="GRADUATION_CAP"
            variant="primary"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Roblox3DMetricCard
            title="Active Classes"
            value={5}
            iconName="BOOKS"
            variant="success"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Roblox3DMetricCard
            title="Avg. Performance"
            value={87}
            change={+3.2}
            iconName="TROPHY"
            variant="warning"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, lg: 3 }}>
          <Roblox3DMetricCard
            title="Pending Reviews"
            value={12}
            iconName="BOARD"
            variant="info"
            animated={true}
          />
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
                  <RobloxProgressBar
                    currentXP={(idx + 1) * 200}
                    requiredXP={1000}
                    level={idx + 1}
                    showLevel={false}
                    animated={true}
                    variant="gradient"
                  />
                  <Roblox3DButton
                    iconName="BOOKS"
                    label="View Class"
                    variant="primary"
                    size="small"
                    fullWidth
                    onClick={() => console.log(`View ${className}`)}
                  />
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
        <Roblox3DNavigation
          items={navItems}
          onItemClick={(item) => setSelectedView(item.id)}
          variant="buttons"
          orientation="horizontal"
          glowEffect={true}
        />
      </Box>

      {/* System Metrics */}
      <Grid gutter="lg" mb="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Roblox3DMetricCard
            title="Total Users"
            value={1247}
            change={+15.3}
            iconName="GRADUATION_CAP"
            variant="primary"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Roblox3DMetricCard
            title="Active Sessions"
            value={342}
            change={+8.1}
            iconName="LIGHT_BULB"
            variant="success"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Roblox3DMetricCard
            title="Courses"
            value={89}
            change={+2}
            iconName="BOOKS"
            variant="info"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Roblox3DMetricCard
            title="Achievements"
            value={456}
            iconName="TROPHY"
            variant="warning"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Roblox3DMetricCard
            title="System Load"
            value={67}
            change={-5.2}
            iconName="BOARD"
            variant="success"
            animated={true}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 4, lg: 2 }}>
          <Roblox3DMetricCard
            title="Uptime"
            value={99.9}
            iconName="LIGHT_BULB"
            variant="success"
            animated={true}
          />
        </Grid.Col>
      </Grid>

      {/* Control Panel */}
      <Card shadow="md" padding="lg" radius="lg">
        <Title order={3} mb="md">System Controls</Title>

        <Grid gutter="md">
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Roblox3DButton
              iconName="GRADUATION_CAP"
              label="User Management"
              variant="primary"
              fullWidth
              onClick={() => console.log('User management')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Roblox3DButton
              iconName="BOOKS"
              label="Content Management"
              variant="secondary"
              fullWidth
              onClick={() => console.log('Content management')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Roblox3DButton
              iconName="LIGHT_BULB"
              label="Analytics"
              variant="info"
              fullWidth
              onClick={() => console.log('Analytics')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Roblox3DButton
              iconName="TROPHY"
              label="Gamification"
              variant="warning"
              fullWidth
              onClick={() => console.log('Gamification')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Roblox3DButton
              iconName="BOARD"
              label="System Settings"
              variant="success"
              fullWidth
              onClick={() => console.log('System settings')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <Roblox3DButton
              iconName="LIGHT_BULB"
              label="Reports"
              variant="primary"
              fullWidth
              onClick={() => console.log('Reports')}
            />
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
              Explore different dashboard layouts built with Roblox components
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
