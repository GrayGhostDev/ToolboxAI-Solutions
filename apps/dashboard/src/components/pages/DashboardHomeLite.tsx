import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
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
import { useAppSelector, useAppDispatch } from '../../store';
import { addXP } from '../../store/slices/gamificationSlice';
import { addNotification } from '../../store/slices/uiSlice';
import { getDashboardOverview } from '../../services/api';
import { type DashboardOverview } from '../../types/api';
import { ROUTES } from '../../config/routes';

// Lazy load heavy components to improve initial load time
const ProgressCharts = lazy(() => import('../widgets/ProgressCharts').then(m => ({ default: m.ProgressCharts })).catch(() => ({ default: () => <Text c="dimmed" size="sm">Charts temporarily unavailable</Text> })));
const RealTimeAnalytics = lazy(() => import('../widgets/RealTimeAnalytics').catch(() => ({ default: () => <Text c="dimmed" size="sm">Real-time analytics temporarily unavailable</Text> })));
const ConnectionStatus = lazy(() => import('../widgets/ConnectionStatus').catch(() => ({ default: () => <Badge color="gray">Offline</Badge> })));
const CreateLessonDialog = lazy(() => import('../dialogs/CreateLessonDialog').catch(() => ({ default: () => null })));

// Lazy load Roblox components that use 3D rendering
const RobloxToolsSection = lazy(() => import('./components/RobloxToolsSection').catch(() => ({ default: () => <Text c="dimmed" size="sm">Roblox tools temporarily unavailable</Text> })));
const RobloxNavigationHub = lazy(() => import('./components/RobloxNavigationHub').catch(() => ({ default: () => <Text c="dimmed" size="sm">Roblox navigation temporarily unavailable</Text> })));

// Simple skeleton for lazy components
const ComponentSkeleton = ({ height = 200 }: { height?: number }) => (
  <Box style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: height }}>
    <Loader size="sm" />
  </Box>
);

export function DashboardHomeLite({ role }: { role?: UserRole }) {
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const xp = useAppSelector((s) => s.gamification?.xp ?? 0);
  const level = useAppSelector((s) => s.gamification?.level ?? 1);
  const streakDays = useAppSelector((s) => s.gamification?.streakDays ?? 0);
  const badgesCount = useAppSelector((s) => (s.gamification?.badges ? s.gamification.badges.length : 0));
  const storeRole = useAppSelector((s) => (s as any).user?.role ?? (s as any).user?.currentUser?.role ?? null);
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
  const effectiveRole = (role ?? storeRole ?? (bypassAuth ? 'teacher' : null)) as UserRole | null;
  const userXP = useAppSelector((s) => (s as any).user?.userId) ? xp : 0;

  const [dashboardData, setDashboardData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createLessonOpen, setCreateLessonOpen] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [show3DComponents, setShow3DComponents] = useState(false);

  // Enable 3D components after a delay to improve initial load
  useEffect(() => {
    const timer = setTimeout(() => setShow3DComponents(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  // Simplified data loader with faster fallback
  const loadDashboardData = useCallback(async (isRetry = false) => {
    const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (!effectiveRole) {
      setLoading(false);
      return;
    }

    // Use mock data immediately for faster loading
    if (bypassAuth || useMockData || retryCount >= 1) {
      // Simplified mock data structure
      setDashboardData({
        role: effectiveRole,
        metrics: {
          totalStudents: 156,
          activeClasses: 8,
          averageProgress: 78
        },
        recentActivity: [
          { id: '1', type: 'lesson_completed', message: 'New lesson completed', timestamp: new Date().toISOString() },
          { id: '2', type: 'achievement', message: 'Badge earned', timestamp: new Date().toISOString() }
        ],
        notifications: [
          { id: '1', type: 'success', message: 'Dashboard loaded successfully!' }
        ],
        kpis: {
          totalStudents: 156,
          activeSessions: 12,
          completedLessons: 89,
          averageScore: 85,
          progressChange: 12
        }
      });
      setLoading(false);
      return;
    }

    try {
      if (!isRetry) {
        setLoading(true);
        setError(null);
      }

      const data = await getDashboardOverview(effectiveRole);
      setDashboardData(data);
      setRetryCount(0);
    } catch (err: any) {
      console.error('Dashboard data load error:', err);

      // Fail fast with mock data to prevent timeouts
      setDashboardData({
        role: effectiveRole,
        metrics: { totalStudents: 0, activeClasses: 0, averageProgress: 0 },
        recentActivity: [],
        notifications: [{ id: '1', type: 'info', message: 'Using offline mode' }],
        kpis: { totalStudents: 0, activeSessions: 0, completedLessons: 0, averageScore: 0, progressChange: 0 }
      });
      setError('Using offline mode - refresh to sync with server.');
    } finally {
      setLoading(false);
    }
  }, [effectiveRole, retryCount]);

  useEffect(() => {
    void loadDashboardData();
  }, [loadDashboardData]);

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
        <Text c="red" size="xl" fw={600}>Dashboard Loading</Text>
        <Text size="sm" style={{ marginBottom: 16 }}>{error}</Text>
        <Group>
          <Button onClick={() => loadDashboardData()} disabled={loading} leftSection={<IconRefresh size={16} />}>
            Retry
          </Button>
        </Group>
      </Box>
    );
  }

  return (
    <>
      <Grid gutter="md">
        {/* Simple Welcome Banner - loads immediately */}
        <Grid.Col span={12}>
          <Card
            style={{
              background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
              color: 'white'
            }}
          >
            <Card.Section p="xl">
              <Stack>
                <Text size="xl" fw={800}>
                  Welcome to ToolboxAI! 🚀
                </Text>
                <Text size="md" style={{ opacity: 0.9 }}>
                  {effectiveRole === 'teacher' && 'Manage classes and create engaging lessons'}
                  {effectiveRole === 'admin' && 'Monitor system performance and manage users'}
                  {effectiveRole === 'student' && 'Continue your learning journey'}
                  {effectiveRole === 'parent' && "Track your child's progress"}
                </Text>

                <Group gap="md">
                  {effectiveRole === 'teacher' && (
                    <>
                      <Button onClick={() => navigate('/roblox-studio')} variant="white" color="dark">
                        Roblox Studio
                      </Button>
                      <Button onClick={() => setCreateLessonOpen(true)} variant="outline" style={{ borderColor: 'white', color: 'white' }}>
                        Create Lesson
                      </Button>
                    </>
                  )}
                  {effectiveRole === 'student' && (
                    <Button onClick={handleCompleteTask} variant="white" color="dark">
                      Start Learning
                    </Button>
                  )}
                  <Button onClick={() => void loadDashboardData()} variant="outline" style={{ borderColor: 'white', color: 'white' }}>
                    Refresh
                  </Button>
                </Group>
              </Stack>
            </Card.Section>
          </Card>
        </Grid.Col>

        {/* Load 3D components after initial render */}
        {show3DComponents && (
          <>
            <Grid.Col span={12}>
              <Suspense fallback={<ComponentSkeleton height={300} />}>
                <RobloxToolsSection />
              </Suspense>
            </Grid.Col>

            <Grid.Col span={12}>
              <Suspense fallback={<ComponentSkeleton height={150} />}>
                <RobloxNavigationHub navigate={navigate} />
              </Suspense>
            </Grid.Col>
          </>
        )}

        {/* Essential metrics - load immediately */}
        {effectiveRole === 'teacher' || effectiveRole === 'admin' ? (
          <>
            <Grid.Col span={{ base: 12, md: 3 }}>
              <Card>
                <Card.Section p="md">
                  <Group align="center" gap="md">
                    <Avatar size="lg" color="blue">
                      <IconSchool size={24} />
                    </Avatar>
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">Active Classes</Text>
                      <Text size="xl" fw={700}>{dashboardData?.kpis?.activeClasses || dashboardData?.metrics?.activeClasses || 0}</Text>
                      <Text size="xs" c="dimmed">{dashboardData?.kpis?.totalStudents || dashboardData?.metrics?.totalStudents || 0} students</Text>
                    </Stack>
                  </Group>
                </Card.Section>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 3 }}>
              <Card>
                <Card.Section p="md">
                  <Group align="center" gap="md">
                    <Avatar size="lg" color="cyan">📚</Avatar>
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">Completed Lessons</Text>
                      <Text size="xl" fw={700}>{dashboardData?.kpis?.completedLessons || 0}</Text>
                      <Text size="xs" c="dimmed">{dashboardData?.kpis?.activeSessions || 0} active now</Text>
                    </Stack>
                  </Group>
                </Card.Section>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 3 }}>
              <Card>
                <Card.Section p="md">
                  <Group align="center" gap="md">
                    <Avatar size="lg" color="violet">
                      <IconTrendingUp size={24} />
                    </Avatar>
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">Avg. Progress</Text>
                      <Text size="xl" fw={700}>{dashboardData?.kpis?.averageProgress || dashboardData?.metrics?.averageProgress || 0}%</Text>
                      <Badge size="sm" color="green">+{dashboardData?.kpis?.progressChange || 0}% this week</Badge>
                    </Stack>
                  </Group>
                </Card.Section>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 3 }}>
              <Card>
                <Card.Section p="md">
                  <Group align="center" gap="md">
                    <Avatar size="lg" color="green">
                      <IconCheck size={24} />
                    </Avatar>
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">Avg. Score</Text>
                      <Text size="xl" fw={700}>{dashboardData?.kpis?.averageScore || 0}%</Text>
                      <Text size="xs" c="dimmed">Last updated today</Text>
                    </Stack>
                  </Group>
                </Card.Section>
              </Card>
            </Grid.Col>
          </>
        ) : effectiveRole === 'student' ? (
          <>
            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card style={{ background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.blue[0]})` }}>
                <Card.Section p="md">
                  <Group align="center" gap="md">
                    <Avatar size="lg" style={{ background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})` }}>🏆</Avatar>
                    <Box>
                      <Text size="lg" fw={700} c={theme.colors.blue[6]}>Experience Points</Text>
                      <Text size="xl" fw={800}>{xp.toLocaleString()}</Text>
                    </Box>
                  </Group>
                  <Progress value={xp % 100} size="lg" radius="xl" color="blue" mt="sm" />
                </Card.Section>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card style={{ background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.orange[0]})` }}>
                <Card.Section p="md">
                  <Group align="center" gap="md">
                    <Avatar size="lg" style={{ background: `linear-gradient(135deg, ${theme.colors.orange[6]}, ${theme.colors.red[6]})` }}>⭐</Avatar>
                    <Box>
                      <Text size="lg" fw={700} c={theme.colors.orange[6]}>Current Level</Text>
                      <Text size="xl" fw={800}>Level {level}</Text>
                    </Box>
                  </Group>
                  <Text size="sm" c="dimmed" mt="xs">{100 - (xp % 100)} XP to next level</Text>
                </Card.Section>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Card style={{ background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${theme.colors.violet[0]})` }}>
                <Card.Section p="md">
                  <Text size="lg" fw={700} c={theme.colors.violet[6]} mb="md">Achievements</Text>
                  <Group gap="xs">
                    <Badge size="lg" variant="gradient" gradient={{ from: 'violet', to: 'blue' }}>🚀 Space Walker</Badge>
                    <Badge size="lg" variant="gradient" gradient={{ from: 'orange', to: 'red' }}>💡 Quiz Master</Badge>
                    <Badge size="lg" variant="gradient" gradient={{ from: 'green', to: 'blue' }}>🏆 Streak Keeper</Badge>
                  </Group>
                </Card.Section>
              </Card>
            </Grid.Col>
          </>
        ) : null}

        {/* Analytics section - lazy loaded */}
        {(effectiveRole === 'admin' || effectiveRole === 'teacher') && (
          <Grid.Col span={12}>
            <Group justify="space-between" align="center" mb="md">
              <Text size="lg" fw={600}>Real-Time Analytics</Text>
              <Suspense fallback={<Loader size="sm" />}>
                <ConnectionStatus showLabel={true} />
              </Suspense>
            </Group>
            <Suspense fallback={<ComponentSkeleton height={300} />}>
              <RealTimeAnalytics />
            </Suspense>
          </Grid.Col>
        )}

        {/* Charts section - lazy loaded */}
        <Grid.Col span={12}>
          <Text size="lg" mb="md" fw={600}>Progress Charts</Text>
          <Suspense fallback={<ComponentSkeleton height={400} />}>
            <ProgressCharts role={(effectiveRole ?? 'student') as UserRole} />
          </Suspense>
        </Grid.Col>

        {/* Recent Activity - simplified */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card>
            <Card.Section p="md">
              <Text size="lg" mb="md" fw={600}>Recent Activity</Text>
              <Stack gap="md">
                {(dashboardData?.recentActivity || []).slice(0, 3).map((activity: any, index) => (
                  <Group key={index} align="center" gap="md" p="sm" style={{ borderRadius: theme.radius.sm, backgroundColor: theme.colors.gray[0] }}>
                    <Avatar size="sm" color="blue">✓</Avatar>
                    <Stack gap="xs" style={{ flex: 1 }}>
                      <Text size="sm">{activity.message || activity.action}</Text>
                      <Text size="xs" c="dimmed">{activity.time || 'Recently'}</Text>
                    </Stack>
                  </Group>
                ))}
              </Stack>
            </Card.Section>
          </Card>
        </Grid.Col>

        {/* Quick Actions */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card>
            <Card.Section p="md">
              <Text size="lg" mb="md" fw={600}>Quick Actions</Text>
              <Stack gap="md">
                <Button fullWidth variant="light" leftSection={<IconRocket size={16} />} onClick={() => navigate('/lessons')}>
                  View All Lessons
                </Button>
                <Button fullWidth variant="light" leftSection={<IconClipboardCheck size={16} />} onClick={() => navigate('/assessments')}>
                  Check Assessments
                </Button>
                <Button fullWidth variant="light" leftSection={<IconTrophy size={16} />} onClick={() => navigate('/rewards')}>
                  View Rewards
                </Button>
              </Stack>
            </Card.Section>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Create Lesson Dialog - lazy loaded */}
      {effectiveRole === 'teacher' && (
        <Suspense fallback={null}>
          <CreateLessonDialog
            open={createLessonOpen}
            onClose={() => setCreateLessonOpen(false)}
            onSuccess={() => {
              setCreateLessonOpen(false);
              dispatch(addNotification({
                type: 'success',
                message: 'Lesson created successfully!'
              }));
            }}
          />
        </Suspense>
      )}
    </>
  );
}

export default DashboardHomeLite;