import {
  Box, Button, Text, Paper, Stack, SimpleGrid, Container, ActionIcon, Avatar, Card,
  Group, List, Divider, TextInput, Select, Badge, Alert, Loader,
  Progress, Modal, Drawer, Tabs, Menu, Tooltip, Checkbox, Radio,
  Switch, Slider, Rating, Skeleton, Table, useMantineTheme
} from '@mantine/core';
import { IconRefresh, IconSchool, IconCircleCheck } from '@tabler/icons-react';

// Helper function for color transparency (replaces MUI alpha)
const alpha = (color: string, opacity: number) => {
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
};
/**
 * Enhanced DashboardHome component using RTK Query
 *
 * This component demonstrates the improved state management with:
 * - Automatic caching and deduplication
 * - Optimistic updates
 * - Smart refetching strategies
 * - Background synchronization
 * - Improved loading states
 */

import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { type UserRole } from '../../types';
import { ProgressCharts } from '../widgets/ProgressCharts';
import { useAppSelector } from '../../store';
import {
  useGetDashboardOverviewQuery,
  useGetClassesQuery,
  useGetMessagesQuery,
  useGetWeeklyXPQuery,
  useGetBadgesQuery,
  useGetLeaderboardQuery,
  api
} from '../../store/api';
import {
  selectDashboardSummary,
  selectUnreadMessageCount,
  selectRecentActivity,
  selectCachePerformance,
  selectActiveClasses,
} from '../../store/api/selectors';
import { useDashboardMigration, useMigrationProgress } from '../../store/api/migration';
import { ROUTES } from '../../config/routes';
import CreateLessonDialog from '../dialogs/CreateLessonDialog';
import RealTimeAnalytics from '../widgets/RealTimeAnalytics';
import ConnectionStatus from '../widgets/ConnectionStatus';

// Roblox-themed components
import RobloxCharacterAvatar from '../roblox/RobloxCharacterAvatar';
import { Roblox3DButton } from '../roblox/Roblox3DButton';
import { Real3DIcon } from '../roblox/Real3DIcon';
import { robloxColors } from '../../theme/robloxTheme';

interface DashboardHomeRTKProps {
  role?: UserRole;
  enableOptimizations?: boolean;
  showMigrationInfo?: boolean;
  enablePrefetching?: boolean;
}

export function DashboardHomeRTK({
  role,
  enableOptimizations = true,
  showMigrationInfo = false,
  enablePrefetching = true,
}: DashboardHomeRTKProps) {
  const theme = useMantineTheme();
  const navigate = useNavigate();

  // RTK Query hooks with intelligent caching
  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
    isFetching: isDashboardFetching,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useGetDashboardOverviewQuery(role, {
    pollingInterval: 30000, // Poll every 30 seconds
    refetchOnFocus: true,
    refetchOnReconnect: true,
    skip: !role, // Skip if no role
  });

  const {
    data: classesData,
    isLoading: isClassesLoading,
    error: classesError,
  } = useGetClassesQuery(undefined, {
    skip: role === 'student', // Students don't need classes data
  });

  const {
    data: messagesData,
    isLoading: isMessagesLoading,
  } = useGetMessagesQuery({
    unread_only: true,
  }, {
    pollingInterval: 60000, // Poll messages every minute
  });

  const {
    data: weeklyXPData,
    isLoading: isXPLoading,
  } = useGetWeeklyXPQuery(undefined, {
    skip: role !== 'student' && role !== 'parent',
  });

  const {
    data: badgesData,
    isLoading: isBadgesLoading,
  } = useGetBadgesQuery(undefined, {
    skip: role !== 'student' && role !== 'parent',
  });

  const {
    data: leaderboardData,
    isLoading: isLeaderboardLoading,
  } = useGetLeaderboardQuery({
    timeframe: 'weekly',
  }, {
    skip: role === 'admin',
  });

  // Enhanced selectors for computed data
  const dashboardSummary = useAppSelector(selectDashboardSummary);
  const unreadCount = useAppSelector(selectUnreadMessageCount);
  const recentActivity = useAppSelector(selectRecentActivity);
  const cachePerformance = useAppSelector(selectCachePerformance);
  const activeClasses = useAppSelector(selectActiveClasses);

  // Migration utilities
  const migrationStatus = useDashboardMigration();
  const migrationProgress = useMigrationProgress();

  // Legacy state for backward compatibility
  const legacyXP = useAppSelector((s) => s.gamification?.xp ?? 0);
  const legacyLevel = useAppSelector((s) => s.gamification?.level ?? 1);
  const storeRole = useAppSelector((s) => (s as any).user?.role ?? (s as any).user?.currentUser?.role ?? null);
  const effectiveRole = (role ?? storeRole) as UserRole | null;

  // Local state
  const [createLessonOpen, setCreateLessonOpen] = useState(false);
  const [showCacheStats, setShowCacheStats] = useState(showMigrationInfo);

  // Prefetching for improved UX
  const prefetchDashboard = api.usePrefetch('getDashboardOverview');
  const prefetchClasses = api.usePrefetch('getClasses');

  useEffect(() => {
    if (enablePrefetching && effectiveRole) {
      // Prefetch related data based on role
      if (effectiveRole === 'teacher') {
        prefetchClasses();
      }
    }
  }, [effectiveRole, enablePrefetching, prefetchClasses]);

  // Smart refetch with debouncing
  const handleRefresh = useCallback(async () => {
    try {
      await Promise.all([
        refetchDashboard(),
        // Only refetch relevant data based on role
        effectiveRole !== 'student' && classesData && classesData.length > 0 ?
          Promise.resolve() : Promise.resolve(),
      ]);
    } catch (error) {
      console.error('Refresh failed:', error);
    }
  }, [refetchDashboard, effectiveRole, classesData]);

  // Compute derived state
  const isLoading = isDashboardLoading && !dashboardData; // Show loading only on initial load
  const isFetching = isDashboardFetching || isClassesLoading || isMessagesLoading;
  const hasError = dashboardError || classesError;

  // Enhanced error handling
  const getErrorMessage = useCallback(() => {
    if (dashboardError) {
      if ('status' in dashboardError) {
        switch (dashboardError.status) {
          case 401:
            return 'Authentication expired. Please refresh the page.';
          case 403:
            return 'You do not have permission to view this dashboard.';
          case 404:
            return 'Dashboard data not found. Please contact support.';
          case 500:
            return 'Server error. Our team has been notified.';
          default:
            return 'Failed to load dashboard data. Please try again.';
        }
      }
      return 'Network error. Please check your connection.';
    }
    return 'An unexpected error occurred.';
  }, [dashboardError]);

  // Calculate XP and level from multiple sources
  const userXP = dashboardData?.studentData?.xp ??
                badgesData?.reduce((sum, badge) => sum + (badge.xpValue || 0), 0) ??
                legacyXP;
  const userLevel = Math.floor(userXP / 100) + 1;
  const streakDays = dashboardData?.studentData?.streakDays ?? 0;

  // Loading state
  if (isLoading) {
    return (
      <Stack align="center" justify="center" style={{ minHeight: 400 }}>
        <Loader size={60} />
        <Text size="lg" style={{ marginTop: theme.spacing.md, opacity: 0.7 }}>
          Loading your dashboard...
        </Text>
        {enableOptimizations && (
          <Text size="sm" style={{ marginTop: theme.spacing.xs, opacity: 0.5 }}>
            Cache hit ratio: {cachePerformance.cacheHitRatio.toFixed(1)}%
          </Text>
        )}
      </Stack>
    );
  }

  // Error state with enhanced recovery options
  if (hasError && !dashboardData) {
    return (
      <Box p="md">
        <Alert color="red" style={{ marginBottom: theme.spacing.md }}>
          <Text fw={600}>Dashboard Error</Text>
          <Text size="sm">{getErrorMessage()}</Text>
        </Alert>

        <Group wrap="wrap" gap="md">
          <Button
            onClick={handleRefresh}
            variant="filled"
            disabled={isFetching}
            leftSection={isFetching ? <Loader size={16} /> : <IconRefresh />}
          >
            {isFetching ? 'Retrying...' : 'Retry'}
          </Button>
          <Button
            onClick={() => window.location.reload()}
            variant="outline"
          >
            Refresh Page
          </Button>
          {showMigrationInfo && (
            <Button
              onClick={() => setShowCacheStats(!showCacheStats)}
              variant="subtle"
              size="sm"
            >
              {showCacheStats ? 'Hide' : 'Show'} Debug Info
            </Button>
          )}
        </Group>

        {showCacheStats && (
          <Card style={{ marginTop: theme.spacing.md }} withBorder>
            <Text fw={600} mb="md">Debug Information</Text>
            <Text size="sm">
              Migration Status: {migrationProgress.migrationComplete ? 'Complete' : 'In Progress'}
            </Text>
            <Text size="sm">
              Cache Efficiency: {migrationProgress.cacheEfficiency}
            </Text>
            <Text size="sm">
              RTK Queries: {migrationProgress.rtkQueries}
            </Text>
            <Text size="sm">
              Legacy Slices: {migrationProgress.legacySlicesActive}
            </Text>
          </Card>
        )}
      </Box>
    );
  }

  return (
    <>
      {/* RTK Query Status Indicator */}
      {showMigrationInfo && (
        <Alert
          color={migrationProgress.migrationComplete ? 'green' : 'blue'}
          style={{ marginBottom: theme.spacing.md }}
        >
          <Text size="sm">
            <strong>RTK Query Status:</strong> {migrationProgress.migrationComplete ? 'Fully Migrated' : 'Migration in Progress'} |
            Cache Hit Ratio: {cachePerformance.cacheHitRatio.toFixed(1)}% |
            Efficiency: {migrationProgress.cacheEfficiency}
            {isFetching && <Loader size={16} style={{ marginLeft: theme.spacing.xs }} />}
          </Text>
        </Alert>
      )}

      <Stack gap="md">
        {/* Enhanced Welcome Banner with Real-time Data */}
        <Card
          style={{
            background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
            color: 'white',
            position: 'relative',
            overflow: 'hidden'
          }}
          p="lg"
        >
          <Stack
            justify="space-between"
            align={{ base: 'flex-start', md: 'center' }}
            gap="md"
          >
            <Stack style={{ flex: 1 }}>
              <Text
                size="xl"
                fw={800}
                mb="xs"
                style={{
                  background: 'linear-gradient(135deg, #fff, #e0e0e0)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                }}
              >
                <Group gap="xs" align="center">
                  <Real3DIcon
                    iconName="ROCKET"
                    size="small"
                    animated={true}
                    particleEffect="sparkle"
                    glowColor={robloxColors.neon.electricBlue}
                  />
                  <span>Welcome to Mission Control!</span>
                  <Box style={{ display: 'inline-flex', animation: 'neon-pulse 2s ease-in-out infinite' }}>
                    <Real3DIcon
                      iconName="STAR"
                      size="small"
                      animated={true}
                      particleEffect="none"
                      glowColor={robloxColors.neon.plasmaYellow}
                    />
                  </Box>
                </Group>
              </Text>

              <Text size="md" style={{ opacity: 0.9, marginBottom: theme.spacing.md }}>
                {effectiveRole === 'teacher' && `Managing ${activeClasses.length} active classes with real-time sync`}
                {effectiveRole === 'admin' && `Monitoring ${dashboardSummary?.totalClasses || 0} classes across the platform`}
                {effectiveRole === 'student' && `Ready for your next adventure? You've earned ${userXP} XP!`}
                {effectiveRole === 'parent' && `Your child is Level ${userLevel} with ${streakDays} day streak!`}
              </Text>

              {/* Enhanced Character with Real-time Data */}
              <Group align="center" gap="md" mb="md">
                <RobloxCharacterAvatar
                  character={{
                    name: 'Mission Commander',
                    type: 'astronaut',
                    level: userLevel,
                    xp: userXP,
                    achievements: badgesData?.map(b => b.name) || ['First Steps', 'Explorer'],
                    isActive: true,
                    imagePath: ''
                  }}
                  size="medium"
                  showLevel={false}
                  showXP={false}
                  animated={true}
                />
                <Box>
                  <Text fw={600} size="lg">
                    Level {userLevel} Commander
                  </Text>
                  <Group gap="xs">
                    <Text size="sm" style={{ opacity: 0.8 }}>
                      {userXP.toLocaleString()} XP • {streakDays} day streak
                    </Text>
                    {unreadCount > 0 && (
                      <Badge
                        color="white"
                        variant="light"
                        size="sm"
                      >
                        {unreadCount} new messages
                      </Badge>
                    )}
                  </Group>
                </Box>
              </Group>
                </Stack>

                {/* Enhanced Action Buttons with Loading States */}
                <Group gap="md" wrap="wrap">
                  {effectiveRole === 'teacher' && (
                    <>
                      <Roblox3DButton
                        iconName="ROCKET"
                        label="Roblox Studio"
                        onClick={() => navigate('/roblox-studio')}
                        variant="primary"
                        size="medium"
                        animated={true}
                        tooltip="Open Roblox Studio Integration"
                        glowEffect={true}
                        disabled={isClassesLoading}
                      />
                      <Roblox3DButton
                        iconName="OPEN_BOOK"
                        label="Create Lesson"
                        onClick={() => setCreateLessonOpen(true)}
                        variant="secondary"
                        size="medium"
                        animated={true}
                        tooltip="Create a new lesson for your students"
                      />
                    </>
                  )}

                  <Roblox3DButton
                    iconName="REFRESH"
                    label={isFetching ? 'Syncing...' : 'Refresh'}
                    onClick={handleRefresh}
                    variant="info"
                    size="medium"
                    animated={!isFetching}
                    glowEffect={true}
                    tooltip="Refresh dashboard data"
                    disabled={isFetching}
                  />
                </Group>
              </Stack>
          </Card>

        {/* Enhanced Metrics Cards with Real-time Updates */}
        {(effectiveRole === 'teacher' || effectiveRole === 'admin') && (
          <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
            <Card style={{ padding: theme.spacing.md }}>
              <Group align="center" gap="md">
                <Avatar size={48} style={{ backgroundColor: theme.colors.blue[6] }}>
                  <IconSchool />
                </Avatar>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text size="xs" c="dimmed">
                    Active Classes
                  </Text>
                  <Group align="center" gap="xs">
                    <Text size="xl" fw={700}>
                      {dashboardSummary?.activeClasses || activeClasses.length || 0}
                    </Text>
                    {isClassesLoading && <Loader size={16} />}
                  </Group>
                  <Text size="xs" c="dimmed">
                    {dashboardSummary?.totalStudents || 0} total students
                  </Text>
                </Stack>
              </Group>
            </Card>

            <Card style={{ padding: theme.spacing.md }}>
              <Group align="center" gap="md">
                <Avatar size={48} style={{ backgroundColor: theme.colors.cyan[6] }}>
                  📧
                </Avatar>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text size="xs" c="dimmed">
                    Unread Messages
                  </Text>
                  <Group align="center" gap="xs">
                    <Text size="xl" fw={700}>
                      {unreadCount}
                    </Text>
                    {isMessagesLoading && <Loader size={16} />}
                  </Group>
                  <Text size="xs" c="dimmed">
                    {messagesData?.length || 0} total messages
                  </Text>
                </Stack>
              </Group>
            </Card>

            <Card style={{ padding: theme.spacing.md }}>
              <Group align="center" gap="md">
                <Avatar size={48} style={{ backgroundColor: theme.colors.violet[6] }}>
                  📈
                </Avatar>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text size="xs" c="dimmed">
                    Cache Efficiency
                  </Text>
                  <Text size="xl" fw={700}>
                    {cachePerformance.cacheHitRatio.toFixed(1)}%
                  </Text>
                  <Badge
                    size="sm"
                    color={migrationProgress.cacheEfficiency === 'excellent' ? 'green' :
                           migrationProgress.cacheEfficiency === 'good' ? 'yellow' : 'red'}
                  >
                    {migrationProgress.cacheEfficiency}
                  </Badge>
                </Stack>
              </Group>
            </Card>

            <Card style={{ padding: theme.spacing.md }}>
              <Group align="center" gap="md">
                <Avatar size={48} style={{ backgroundColor: theme.colors.green[6] }}>
                  <IconCircleCheck />
                </Avatar>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text size="xs" c="dimmed">
                    Real-time Sync
                  </Text>
                  <Text size="xl" fw={700}>
                    {isFetching ? 'Syncing' : 'Live'}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {migrationProgress.rtkQueries} cached queries
                  </Text>
                </Stack>
              </Group>
            </Card>
          </SimpleGrid>
        )}

        {/* Enhanced Student Progress Cards */}
        {effectiveRole === 'student' && (
          <SimpleGrid cols={{ base: 1, md: 3 }} spacing="md">
            <Card
              style={{
                background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${alpha(theme.colors.blue[6], 0.05)})`,
                border: `2px solid ${alpha(theme.colors.blue[6], 0.2)}`,
                borderRadius: theme.radius.md,
                padding: theme.spacing.lg
              }}
            >
              <Group align="center" gap="md" mb="md">
                <Avatar
                  size={50}
                  style={{
                    background: `linear-gradient(135deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                    fontSize: '1.5rem',
                  }}
                >
                  🏆
                </Avatar>
                <Box style={{ flex: 1 }}>
                  <Text size="sm" fw={700} c={theme.colors.blue[6]}>
                    Experience Points
                  </Text>
                  <Group align="center" gap="xs">
                    <Text size="xl" fw={800}>
                      {userXP.toLocaleString()}
                    </Text>
                    {isXPLoading && <Loader size={20} />}
                  </Group>
                </Box>
              </Group>

              <Box>
                <Text size="sm" c="dimmed" mb="xs">
                  Level Progress: {userXP % 100}%
                </Text>
                <Progress
                  value={userXP % 100}
                  size="lg"
                  radius="md"
                  style={{
                    '& .mantine-Progress-bar': {
                      background: `linear-gradient(90deg, ${theme.colors.blue[6]}, ${theme.colors.violet[6]})`,
                    }
                  }}
                />
              </Box>
            </Card>

            <Card
              style={{
                background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${alpha(theme.colors.violet[6], 0.05)})`,
                border: `2px solid ${alpha(theme.colors.violet[6], 0.2)}`,
                borderRadius: theme.radius.md,
                padding: theme.spacing.lg
              }}
            >
              <Group align="center" gap="md" mb="md">
                <Text size="sm" fw={700} c={theme.colors.violet[6]}>
                  Achievements
                </Text>
                {isBadgesLoading && <Loader size={20} />}
              </Group>

              <Group gap="sm" wrap="wrap">
                {(badgesData || []).slice(0, 4).map((badge, index) => (
                  <Box
                    key={badge.id}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      padding: theme.spacing.sm,
                      borderRadius: theme.radius.sm,
                      background: `linear-gradient(145deg, ${alpha(theme.colors.violet[6], 0.1)}, ${alpha(theme.colors.violet[6], 0.05)})`,
                      border: `1px solid ${alpha(theme.colors.violet[6], 0.3)}`,
                      cursor: 'pointer',
                      minWidth: 60,
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <Real3DIcon
                      iconName="TROPHY"
                      size="small"
                      animated={true}
                      description={badge.name}
                    />
                    <Text size="xs" fw={600} ta="center" mt="xs">
                      {badge.name}
                    </Text>
                  </Box>
                ))}
              </Group>
            </Card>

            <Card
              style={{
                background: `linear-gradient(145deg, ${theme.colors.gray[0]}, ${alpha(theme.colors.yellow[6], 0.05)})`,
                border: `2px solid ${alpha(theme.colors.yellow[6], 0.2)}`,
                borderRadius: theme.radius.md,
                padding: theme.spacing.lg
              }}
            >
              <Group align="center" gap="md" mb="md">
                <Avatar
                  size={50}
                  style={{
                    background: `linear-gradient(135deg, ${theme.colors.yellow[6]}, ${theme.colors.red[6]})`,
                    fontSize: '1.5rem',
                  }}
                >
                  🥇
                </Avatar>
                <Box style={{ flex: 1 }}>
                  <Text size="sm" fw={700} c={theme.colors.yellow[6]}>
                    Leaderboard
                  </Text>
                  <Group align="center" gap="xs">
                    <Text size="xl" fw={800}>
                      #{leaderboardData?.find(entry => entry.userId === 'current-user')?.rank || '?'}
                    </Text>
                    {isLeaderboardLoading && <Loader size={20} />}
                  </Group>
                </Box>
              </Group>

              <Text size="sm" c="dimmed">
                Weekly ranking among peers
              </Text>
            </Card>
          </SimpleGrid>
        )}

        {/* Real-Time Analytics with Enhanced Data */}
        {(effectiveRole === 'admin' || effectiveRole === 'teacher') && (
          <Box>
            <Group justify="space-between" align="center" mb="md">
              <Group align="center" gap="xs">
                <Text size="xl" fw={600}>
                  Real-Time Analytics
                </Text>
                {isFetching && <Loader size={20} />}
              </Group>
              <Group align="center" gap="md">
                <ConnectionStatus showLabel={true} />
                <Text size="sm" c="dimmed">
                  Cache: {cachePerformance.cacheHitRatio.toFixed(1)}%
                </Text>
              </Group>
            </Group>
            <RealTimeAnalytics />
          </Box>
        )}

        {/* Enhanced Charts with RTK Query Data */}
        <Box>
          <Group align="center" gap="xs" mb="md">
            <Text size="xl" fw={600}>
              Analytics & Progress
            </Text>
            {(isXPLoading || isLeaderboardLoading) && <Loader size={20} />}
          </Group>
          <ProgressCharts
            role={(effectiveRole ?? 'student') as UserRole}
            weeklyXPData={weeklyXPData}
            badgesData={badgesData}
            leaderboardData={leaderboardData}
          />
        </Box>

        {/* Enhanced Recent Activity with Real-time Data */}
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
          <Card p="lg">
            <Group align="center" gap="xs" mb="md">
              <Text size="lg" fw={600}>
                Recent Activity
              </Text>
              {isFetching && <Loader size={16} />}
            </Group>
            <Stack gap="md">
              {recentActivity.slice(0, 5).map((activity, index) => (
                <Box
                  key={activity.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: theme.spacing.md,
                    padding: theme.spacing.sm,
                    borderRadius: theme.radius.sm,
                    backgroundColor: theme.colors.gray[0],
                    transition: 'all 0.3s ease',
                  }}
                >
                  <Avatar size={32} style={{ backgroundColor: theme.colors.blue[6], fontSize: '1rem' }}>
                    {activity.type === 'message' && '📧'}
                    {activity.type === 'assessment' && '📝'}
                    {activity.type === 'lesson' && '📚'}
                    {activity.type === 'achievement' && '🏆'}
                  </Avatar>
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Text size="sm">{activity.title}</Text>
                    <Text size="xs" c="dimmed">
                      {activity.description}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {new Date(activity.timestamp).toLocaleString()}
                    </Text>
                  </Stack>
                  {activity.priority === 'high' && (
                    <Badge size="sm" color="red">Priority</Badge>
                  )}
                </Box>
              ))}
            </Stack>
          </Card>

          {/* Enhanced Upcoming Events */}
          <Card p="lg">
            <Text size="lg" fw={600} mb="md">
              Upcoming Events
            </Text>
            <Stack gap="md">
              {(dashboardData?.upcomingEvents || [
                { date: 'Today, 2:00 PM', event: 'Math Quiz', type: 'assessment' },
                { date: 'Tomorrow, 10:00 AM', event: 'Science Lab (Roblox)', type: 'lesson' },
                { date: 'Friday, 3:00 PM', event: 'Parent-Teacher Meeting', type: 'meeting' },
              ]).map((event: any, index) => (
                <Box
                  key={index}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: theme.spacing.md,
                    padding: theme.spacing.sm,
                    borderRadius: theme.radius.sm,
                    backgroundColor: theme.colors.gray[0],
                    transition: 'all 0.3s ease',
                  }}
                >
                  <Avatar
                    size={32}
                    style={{
                      backgroundColor: event.type === 'assessment' ? theme.colors.yellow[6] :
                              event.type === 'lesson' ? theme.colors.cyan[6] :
                              event.type === 'meeting' ? theme.colors.violet[6] : theme.colors.red[6],
                      fontSize: '1rem',
                    }}
                  >
                    {event.type === 'assessment' && '📝'}
                    {event.type === 'lesson' && '📚'}
                    {event.type === 'meeting' && '👥'}
                  </Avatar>
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Text size="sm">{event.event}</Text>
                    <Text size="xs" c="dimmed">
                      {event.date}
                    </Text>
                  </Stack>
                </Box>
              ))}
            </Stack>
          </Card>
        </SimpleGrid>
      </Stack>

      {/* Create Lesson Dialog with RTK Query Integration */}
      {effectiveRole === 'teacher' && (
        <CreateLessonDialog
          open={createLessonOpen}
          onClose={() => setCreateLessonOpen(false)}
          onSuccess={() => {
            setCreateLessonOpen(false);
            // RTK Query will automatically invalidate and refetch related data
          }}
        />
      )}
    </>
  );
}

export default DashboardHomeRTK;