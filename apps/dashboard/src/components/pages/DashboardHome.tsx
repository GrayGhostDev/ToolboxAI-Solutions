import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Card,
  Text,
  Progress,
  Avatar,
  Stack,
  Button,
  Box,
  Badge,
  Loader,
  Group,
  Divider,
  ActionIcon,
  Container
} from '@mantine/core';
import {
  IconRefresh,
  IconTrophy,
  IconTrendingUp,
  IconCheck,
  IconRocket,
  IconSchool,
  IconDeviceGamepad,
  IconClipboardCheck
} from '@tabler/icons-react';
import { useMantineTheme } from '@mantine/core';
import { type UserRole } from '../../types';
import { ProgressCharts } from '../widgets/ProgressCharts';
import { useAppSelector, useAppDispatch } from '../../store';
import { addXP } from '../../store/slices/gamificationSlice';
import { addNotification } from '../../store/slices/uiSlice';
import { type DashboardOverview } from '../../types/api';
import { useApiCallOnMount, useApiCall } from '../../hooks/useApiCall';
import { ROUTES } from '../../config/routes';
import CreateLessonDialog from '../dialogs/CreateLessonDialog';
import RealTimeAnalytics from '../widgets/RealTimeAnalytics';
import ConnectionStatus from '../widgets/ConnectionStatus';
// Roblox-themed components temporarily disabled for Vercel build
// import RobloxCharacterAvatar from '../roblox/RobloxCharacterAvatar';
// import Roblox3DIcon from '../roblox/Roblox3DIcon';
// import { Roblox3DButton } from '../roblox/Roblox3DButton';
// import { Roblox3DTabs } from '../roblox/Roblox3DTabs';
// import { Roblox3DNavigation } from '../roblox/Roblox3DNavigation';
// import { RobloxProgressBar } from '../roblox/RobloxProgressBar';
// import { RobloxAchievementBadge } from '../roblox/RobloxAchievementBadge';
// import { Simple3DIcon } from '../roblox/Simple3DIcon';
// import { Real3DIcon } from '../roblox/Safe3DIcon';
import { robloxColors } from '../../theme/robloxTheme';
import { getDashboardOverview } from '../../services/api';

export function DashboardHome({ role }: { role?: UserRole }) {
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const xp = useAppSelector((s) => s.gamification?.xp ?? 0);
  const level = useAppSelector((s) => s.gamification?.level ?? 1);
  const streakDays = useAppSelector((s) => s.gamification?.streakDays ?? 0);
  const badgesCount = useAppSelector((s) => (s.gamification?.badges ? s.gamification.badges.length : 0));
  const storeRole = useAppSelector((s) => (s as any).user?.role ?? (s as any).user?.currentUser?.role ?? null);
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
  // In bypass mode, always use teacher role as default
  const effectiveRole = (role ?? storeRole ?? (bypassAuth ? 'teacher' : null)) as UserRole | null;
  const userXP = useAppSelector((s) => (s as any).user?.userId) ? xp : 0;

  const [createLessonOpen, setCreateLessonOpen] = useState(false);

  // Fetch dashboard data using API hook
  const {
    data: dashboardData,
    loading,
    error,
    refetch: loadDashboardData
  } = useApiCallOnMount(
    effectiveRole ? `/dashboard/${effectiveRole}` : null,
    {
      mockEndpoint: '/dashboard/overview',
      showNotification: false,
      retryAttempts: 3,
      retryDelay: 2000
    }
  );

  // Navigate to Play page for students
  const handleCompleteTask = () => {
    if (effectiveRole === 'student') {
      navigate('/play');
    } else {
      dispatch(addXP({ amount: 25, reason: 'Completed daily task', source: 'achievement' }));
    }
  };

  if (loading) {
    return (
      <Box style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Loader />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={20}>
        <Text c="red" size="xl" fw={600}>Error loading dashboard</Text>
        <Text size="sm" style={{ marginBottom: 16 }}>
          {typeof error === 'string' ? error : 'Failed to load dashboard data. Please try again.'}
        </Text>
        <Group>
          <Button
            onClick={() => loadDashboardData()}
            variant="filled"
            disabled={loading}
            leftSection={loading ? <Loader size={16} /> : <IconRefresh size={16} />}
          >
            {loading ? 'Retrying...' : 'Retry'}
          </Button>
          <Button
            onClick={() => window.location.reload()}
            variant="outline"
          >
            Refresh Page
          </Button>
        </Group>
      </Box>
    );
  }

  return (
    <>
      <Grid gutter="md">
      {/* Roblox-themed Welcome Banner */}
      <Grid.Col span={12}>
        <Card
          style={{
            background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Card.Section p="xl">
            <Stack
              justify="space-between"
              align="center"
              gap="md"
            >
              <Stack style={{ flex: 1 }}>
                <Text
                  component="div"
                  size="xl"
                  fw={800}
                  style={{
                    background: 'linear-gradient(135deg, #fff, #e0e0e0)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                  }}
                >
                  <Group align="center" gap="xs">
                    <IconRocket size={16} />
                    <span>Welcome to Space Station!</span>
                    <Box style={{ display: 'inline-flex', animation: 'neon-pulse 2s ease-in-out infinite' }}>
                      <IconTrophy size={16} />
                    </Box>
                  </Group>
                </Text>
                <Text size="md" style={{ opacity: 0.9, marginBottom: 16 }}>
                  {role === 'teacher' && "Review today's classes, push lessons to Roblox, and track assessments."}
                  {role === 'admin' && 'Monitor usage across schools, manage integrations, and review compliance.'}
                  {role === 'student' && 'Jump into your next mission, level up, and check the leaderboard!'}
                  {role === 'parent' && "See your child's progress, download reports, and message teachers."}
                </Text>

                {/* Character Avatar */}
                <Group align="center" gap="md" style={{ marginBottom: 16 }}>
                  <Avatar
                    size="lg"
                    style={{
                      background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                    }}
                  >
                    🚀
                  </Avatar>
                  <Box>
                    <Text size="lg" fw={600}>
                      Level {level} Explorer
                    </Text>
                    <Text size="sm" style={{ opacity: 0.8 }}>
                      {userXP} XP • {streakDays} day streak
                    </Text>
                  </Box>
                </Group>
              </Stack>
              <Group gap="md" wrap="wrap">
                {role === 'teacher' && (
                  <>
                    <Button
                      onClick={() => navigate('/roblox-studio')}
                      variant="filled"
                      size="md"
                      leftSection={<IconRocket size={16} />}
                    >
                      Roblox Studio
                    </Button>
                    <Button
                      onClick={() => setCreateLessonOpen(true)}
                      variant="filled"
                      size="md"
                      leftSection={<IconSchool size={16} />}
                    >
                      Create Lesson
                    </Button>
                    <Button
                      onClick={() => navigate(ROUTES.ASSESSMENTS)}
                      variant="filled"
                      size="md"
                      leftSection={<IconClipboardCheck size={16} />}
                    >
                      View Assessments
                    </Button>
                  </>
                )}
                {role === 'admin' && (
                  <>
                    <Button
                      onClick={() => navigate(ROUTES.ANALYTICS)}
                      variant="filled"
                      size="md"
                      leftSection={<IconTrendingUp size={16} />}
                    >
                      Analytics
                    </Button>
                    <Button
                      onClick={() => navigate(ROUTES.INTEGRATIONS)}
                      variant="filled"
                      size="md"
                      leftSection={<IconDeviceGamepad size={16} />}
                    >
                      Manage LMS
                    </Button>
                  </>
                )}
                {role === 'student' && (
                  <>
                    <Button
                      onClick={handleCompleteTask}
                      variant="filled"
                      size="md"
                      leftSection={<IconRocket size={16} />}
                    >
                      Enter Roblox World
                    </Button>
                    <Button
                      onClick={() => navigate(ROUTES.REWARDS)}
                      variant="filled"
                      size="md"
                      leftSection={<IconTrophy size={16} />}
                    >
                      View Rewards
                    </Button>
                  </>
                )}
                {role === 'parent' && (
                  <>
                    <Button
                      onClick={() => navigate('/gameplay-replay')}
                      variant="filled"
                      size="md"
                      leftSection={<IconDeviceGamepad size={16} />}
                    >
                      Watch Gameplay
                    </Button>
                    <Button
                      onClick={() => navigate(ROUTES.REPORTS)}
                      variant="filled"
                      size="md"
                      leftSection={<IconClipboardCheck size={16} />}
                    >
                      View Reports
                    </Button>
                  </>
                )}
                <Button
                  onClick={() => void loadDashboardData()}
                  variant="outline"
                  size="md"
                  leftSection={<IconRefresh size={16} />}
                >
                  Refresh
                </Button>
              </Group>
            </Stack>
          </Card.Section>
        </Card>
      </Grid.Col>

      {/* 3D Educational Tools Section */}
      <Grid.Col span={12}>
        <Card
          style={{
            background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
            border: `2px solid ${theme.colors.blue[2]}`,
            borderRadius: theme.radius.md,
            overflow: 'hidden'
          }}
        >
          <Card.Section p="xl">
            <Text
              component="div"
              size="xl"
              fw={700}
              style={{
                marginBottom: 24,
                textAlign: 'center',
                background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              <Group justify="center" align="center" gap="xs">
                <IconDeviceGamepad size={16} />
                <span>Your Learning Tools</span>
              </Group>
            </Text>

            <Grid gutter="md" justify="center">
              {[
                { icon: '🎲', description: 'ABC Learning Cube' },
                { icon: '📋', description: 'Math Learning Board' },
                { icon: '🚀', description: 'Space Quiz Mission' },
                { icon: '⚽', description: 'Sports Challenge' },
                { icon: '🎨', description: 'Art Studio' },
                { icon: '🏆', description: 'Achievements Hall' },
              ].map((tool, index) => (
                <Grid.Col span={{ base: 6, sm: 4, md: 2 }} key={index}>
                  <Box
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      padding: 16,
                      borderRadius: theme.radius.md,
                      background: `linear-gradient(145deg, ${theme.colors.blue[1]}, ${theme.colors.violet[0]})`,
                      border: `2px solid ${theme.colors.blue[3]}`,
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                    }}
                    onClick={() => console.log(`Clicked ${tool.description}`)}
                  >
                    <Text size="48px" style={{ lineHeight: 1 }}>
                      {tool.icon}
                    </Text>
                    <Text size="sm" ta="center" fw={600} mt="xs">
                      {tool.description}
                    </Text>
                  </Box>
                </Grid.Col>
              ))}
            </Grid>
          </Card.Section>
        </Card>
      </Grid.Col>

      {/* Navigation Section */}
      <Grid.Col span={12}>
        <Card
          style={{
            background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
            border: `2px solid ${theme.colors.blue[2]}`,
            borderRadius: theme.radius.md,
            padding: 16,
          }}
        >
          <Box mb="md">
            <Group justify="center" align="center" gap="xs">
              <IconSchool size={16} />
              <Text size="lg" ta="center" fw={700} component="span">Navigation Hub</Text>
            </Group>
          </Box>
          <Group justify="center" gap="md" wrap="wrap">
            {[
              { name: 'Dashboard', icon: IconSchool, path: '/dashboard' },
              { name: 'Lessons', icon: IconSchool, path: '/lessons', badge: 3 },
              { name: 'Assessments', icon: IconClipboardCheck, path: '/assessments' },
              { name: 'Rewards', icon: IconTrophy, path: '/rewards', badge: 5 },
              { name: 'Profile', icon: IconRocket, path: '/profile' },
            ].map((item, index) => (
              <Button
                key={index}
                variant="filled"
                leftSection={<item.icon size={16} />}
                onClick={() => navigate(item.path)}
                style={{
                  background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                  borderRadius: theme.radius.sm,
                  padding: '8px 24px',
                  textTransform: 'none',
                  fontWeight: 600,
                }}
              >
                {item.name}
                {item.badge && (
                  <Badge
                    size="sm"
                    style={{
                      marginLeft: 8,
                      backgroundColor: theme.colors.red[6],
                      color: 'white',
                      fontSize: '0.7rem',
                    }}
                  >
                    {item.badge}
                  </Badge>
                )}
              </Button>
            ))}
          </Group>
        </Card>
      </Grid.Col>

      {/* 3D Progress and Achievement Cards */}
      {role === 'student' && (
        <>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card
              role="region"
              aria-label="XP overview"
              style={{
                background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})`,
                border: `2px solid ${theme.colors.blue[2]}`,
                borderRadius: theme.radius.md,
                overflow: 'hidden'
              }}
            >
              <Card.Section p="md">
                <Group align="center" gap="md" mb="md">
                  <Avatar
                    size="lg"
                    style={{
                      background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                      border: `2px solid ${theme.colors.blue[6]}`,
                    }}
                  >
                    🏆
                  </Avatar>
                  <Box>
                    <Text size="lg" fw={700} c={theme.colors.blue[6]}>
                      Experience Points
                    </Text>
                    <Text size="xl" fw={800}>
                      {xp.toLocaleString()}
                    </Text>
                  </Box>
                </Group>

                <Box mb="xs">
                  <Text size="sm" c="dimmed" mb="xs">
                    Level Progress: {xp % 100}%
                  </Text>
                  <Progress
                    value={xp % 100}
                    size="lg"
                    radius="xl"
                    color="blue"
                  />
                </Box>
              </Card.Section>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card
              role="region"
              aria-label="Level status"
              style={{
                background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.orange[0]})`,
                border: `2px solid ${theme.colors.orange[2]}`,
                borderRadius: theme.radius.md,
                overflow: 'hidden'
              }}
            >
              <Card.Section p="md">
                <Group align="center" gap="md" mb="md">
                  <Avatar
                    size="lg"
                    style={{
                      background: `linear-gradient(135deg, ${theme.colors.orange[6]}, ${theme.colors.red[6]})`,
                      border: `2px solid ${theme.colors.orange[6]}`,
                    }}
                  >
                    ⭐
                  </Avatar>
                  <Box>
                    <Text size="lg" fw={700} c={theme.colors.orange[6]}>
                      Current Level
                    </Text>
                    <Text size="xl" fw={800}>
                      Level {level}
                    </Text>
                  </Box>
                </Group>

                <Text size="sm" c="dimmed" mb="xs">
                  {100 - (xp % 100)} XP to next level
                </Text>

                <Box mb="xs">
                  <Progress
                    value={100 - (xp % 100)}
                    size="lg"
                    radius="xl"
                    color="orange"
                  />
                </Box>
              </Card.Section>
            </Card>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card
              role="region"
              aria-label="Achievements"
              style={{
                background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.violet[0]})`,
                border: `2px solid ${theme.colors.violet[2]}`,
                borderRadius: theme.radius.md,
                overflow: 'hidden'
              }}
            >
              <Card.Section p="md">
                <Text size="lg" fw={700} c={theme.colors.violet[6]} mb="md">
                  Recent Achievements
                </Text>

                <Group gap="md" wrap="wrap">
                  {[
                    { icon: '🚀', description: 'Space Walker' },
                    { icon: '💡', description: 'Quiz Master' },
                    { icon: '🏆', description: 'Streak Keeper' },
                    { icon: '⭐', description: 'Level Up' },
                  ].map((achievement, index) => (
                    <Box
                      key={index}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        padding: 12,
                        borderRadius: theme.radius.sm,
                        background: `linear-gradient(145deg, ${theme.colors.violet[1]}, ${theme.colors.violet[0]})`,
                        border: `2px solid ${theme.colors.violet[3]}`,
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        minWidth: 80,
                      }}
                      onClick={() => console.log('Achievement clicked:', achievement.description)}
                    >
                      <Text size="32px" style={{ lineHeight: 1 }}>
                        {achievement.icon}
                      </Text>
                      <Text size="xs" ta="center" fw={600} mt={4}>
                        {achievement.description}
                      </Text>
                    </Box>
                  ))}
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
        </>
      )}

      {(role === 'teacher' || role === 'admin') && (
        <>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Active classes">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="blue">
                    <IconSchool size={24} />
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Active Classes
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.kpis?.activeClasses || 0}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {dashboardData?.kpis?.totalStudents || 0} total students
                    </Text>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Lessons scheduled">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="cyan">
                    📚
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Today's Lessons
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.kpis?.todaysLessons || 0}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {dashboardData?.kpis?.pendingAssessments || 0} assessments due
                    </Text>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Average progress">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="violet">
                    <IconTrendingUp size={24} />
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Avg. Progress
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.kpis?.averageProgress || 0}%
                    </Text>
                    <Badge
                      size="sm"
                      color={((dashboardData?.kpis?.progressChange || 0) >= 0) ? 'green' : 'red'}
                      style={{ marginTop: 4 }}
                    >
                      {dashboardData?.kpis?.progressChange || 0}% this week
                    </Badge>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Compliance status">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="green">
                    <IconCheck size={24} />
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Compliance
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.compliance?.status || 'Unknown'}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {dashboardData?.compliance?.pendingAlerts || 0} pending alerts
                    </Text>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
        </>
      )}

      {role === 'parent' && (
        <>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Child's XP">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="blue">
                    <IconTrendingUp size={24} />
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Child's XP
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.studentData?.xp || userXP}
                    </Text>
                    <Text size="xs" c="dimmed">
                      Level {Math.floor((dashboardData?.studentData?.xp || userXP) / 100) + 1}
                    </Text>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Overall progress">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="violet">
                    📊
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Overall Progress
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.studentData?.overallProgress || 0}%
                    </Text>
                    <Badge
                      size="sm"
                      color="green"
                      style={{ marginTop: 4 }}
                    >
                      {dashboardData?.studentData?.performanceRating || 'Average'}
                    </Badge>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Assignments completed">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="cyan">
                    <IconCheck size={24} />
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Assignments
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.studentData?.completedAssignments || 0}/{dashboardData?.studentData?.totalAssignments || 0}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {(dashboardData?.studentData?.totalAssignments || 0) - (dashboardData?.studentData?.completedAssignments || 0)} pending
                    </Text>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 3 }}>
            <Card role="region" aria-label="Last active">
              <Card.Section p="md">
                <Group align="center" gap="md">
                  <Avatar size="lg" color="green">
                    ✅
                  </Avatar>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Last Active
                    </Text>
                    <Text size="xl" fw={700}>
                      {dashboardData?.studentData?.lastActive ? new Date(dashboardData.studentData.lastActive).toLocaleDateString() : 'Today'}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {dashboardData?.studentData?.lastActive ? new Date(dashboardData.studentData.lastActive).toLocaleTimeString() : 'Recently'}
                    </Text>
                  </Stack>
                </Group>
              </Card.Section>
            </Card>
          </Grid.Col>
        </>
      )}

      {/* Real-Time Analytics for Admin and Teacher */}
      {(role === 'admin' || role === 'teacher') && (
        <Grid.Col span={12}>
          <Group justify="space-between" align="center" mb="md">
            <Text size="lg" fw={600}>
              Real-Time Analytics
            </Text>
            <ConnectionStatus showLabel={true} />
          </Group>
          <RealTimeAnalytics />
        </Grid.Col>
      )}

      {/* Charts Section */}
      <Grid.Col span={12}>
        <Text size="lg" mb="md" fw={600}>
          Analytics & Progress
        </Text>
        <ProgressCharts role={(effectiveRole ?? 'student') as UserRole} />
      </Grid.Col>

      {/* Recent Activity */}
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card>
          <Card.Section p="md">
            <Text size="lg" mb="md" fw={600}>
              Recent Activity
            </Text>
            <Stack gap="md">
              {(dashboardData?.recentActivity || [
                { time: '2 hours ago', action: 'Completed Math Lesson', type: 'success' },
                { time: '5 hours ago', action: "Earned 'Problem Solver' badge", type: 'achievement' },
                { time: 'Yesterday', action: 'Submitted Science Assignment', type: 'info' },
                { time: '2 days ago', action: 'Joined Roblox Chemistry Lab', type: 'game' },
              ]).map((activity: any, index) => (
                <Group
                  key={index}
                  align="center"
                  gap="md"
                  p="md"
                  style={{
                    borderRadius: theme.radius.sm,
                    backgroundColor: theme.colors.gray[0],
                  }}
                >
                  <Avatar size="sm" color="blue">
                    {activity.type === 'success' && '✓'}
                    {activity.type === 'achievement' && '🏆'}
                    {activity.type === 'info' && '📝'}
                    {activity.type === 'game' && '🎮'}
                  </Avatar>
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Text size="sm">{activity.action}</Text>
                    <Text size="xs" c="dimmed">
                      {activity.time}
                    </Text>
                  </Stack>
                </Group>
              ))}
            </Stack>
          </Card.Section>
        </Card>
      </Grid.Col>

      {/* Upcoming Events */}
      <Grid.Col span={{ base: 12, md: 6 }}>
        <Card>
          <Card.Section p="md">
            <Text size="lg" mb="md" fw={600}>
              Upcoming Events
            </Text>
            <Stack gap="md">
              {(dashboardData?.upcomingEvents || [
                { date: 'Today, 2:00 PM', event: 'Math Quiz', type: 'assessment' },
                { date: 'Tomorrow, 10:00 AM', event: 'Science Lab (Roblox)', type: 'lesson' },
                { date: 'Friday, 3:00 PM', event: 'Parent-Teacher Meeting', type: 'meeting' },
                { date: 'Next Monday', event: 'History Project Due', type: 'deadline' },
              ]).map((event: any, index) => (
                <Group
                  key={index}
                  align="center"
                  gap="md"
                  p="md"
                  style={{
                    borderRadius: theme.radius.sm,
                    backgroundColor: theme.colors.gray[0],
                  }}
                >
                  <Avatar
                    size="sm"
                    color={
                      event.type === 'assessment'
                        ? 'orange'
                        : event.type === 'lesson'
                        ? 'cyan'
                        : event.type === 'meeting'
                        ? 'violet'
                        : 'red'
                    }
                  >
                    {event.type === 'assessment' && '📝'}
                    {event.type === 'lesson' && '📚'}
                    {event.type === 'meeting' && '👥'}
                    {event.type === 'deadline' && '⏰'}
                  </Avatar>
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Text size="sm">{event.event}</Text>
                    <Text size="xs" c="dimmed">
                      {event.date}
                    </Text>
                  </Stack>
                </Group>
              ))}
            </Stack>
          </Card.Section>
        </Card>
      </Grid.Col>
      </Grid>

      {/* Create Lesson Dialog for Teachers */}
      {role === 'teacher' && (
        <CreateLessonDialog
          open={createLessonOpen}
          onClose={() => setCreateLessonOpen(false)}
          onSuccess={() => {
            setCreateLessonOpen(false);
            dispatch(
              addNotification({
                type: 'success',
                message: 'Lesson created successfully!',
              })
            );
          }}
        />
      )}
    </>
  );
}

export default DashboardHome;