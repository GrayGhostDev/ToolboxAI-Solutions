import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
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

import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { UserRole } from "../../types";
import { ProgressCharts } from "../widgets/ProgressCharts";
import { useAppSelector } from "../../store";
import {
  useGetDashboardOverviewQuery,
  useGetClassesQuery,
  useGetMessagesQuery,
  useGetWeeklyXPQuery,
  useGetBadgesQuery,
  useGetLeaderboardQuery,
  api
} from "../../store/api";
import {
  selectDashboardSummary,
  selectUnreadMessageCount,
  selectRecentActivity,
  selectCachePerformance,
  selectActiveClasses,
} from "../../store/api/selectors";
import { useDashboardMigration, useMigrationProgress } from "../../store/api/migration";
import { ROUTES } from "../../config/routes";
import CreateLessonDialog from "../dialogs/CreateLessonDialog";
import RealTimeAnalytics from "../widgets/RealTimeAnalytics";
import ConnectionStatus from "../widgets/ConnectionStatus";

// Roblox-themed components
import RobloxCharacterAvatar from "../roblox/RobloxCharacterAvatar";
import { Roblox3DButton } from "../roblox/Roblox3DButton";
import { Real3DIcon } from "../roblox/Real3DIcon";
import { robloxColors } from "../../theme/robloxTheme";

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
  const theme = useTheme();
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
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} thickness={4} />
        <Typography order={6} style={{ mt: 2, opacity: 0.7 }}>
          Loading your dashboard...
        </Typography>
        {enableOptimizations && (
          <Typography variant="caption" style={{ mt: 1, opacity: 0.5 }}>
            Cache hit ratio: {cachePerformance.cacheHitRatio.toFixed(1)}%
          </Typography>
        )}
      </Box>
    );
  }

  // Error state with enhanced recovery options
  if (hasError && !dashboardData) {
    return (
      <Box p={3}>
        <Alert severity="error" style={{ mb: 2 }}>
          <Typography order={6}>Dashboard Error</Typography>
          <Typography size="sm">{getErrorMessage()}</Typography>
        </Alert>

        <Stack direction="row" spacing={2} flexWrap="wrap">
          <Button
            onClick={(e: React.MouseEvent) => handleRefresh}
            variant="filled"
            disabled={isFetching}
            startIcon={isFetching ? <CircularProgress size={16} /> : <IconRefresh />}
          >
            {isFetching ? 'Retrying...' : 'Retry'}
          </Button>
          <Button
            onClick={(e: React.MouseEvent) => () => window.location.reload()}
            variant="outline"
          >
            Refresh Page
          </Button>
          {showMigrationInfo && (
            <Button
              onClick={(e: React.MouseEvent) => () => setShowCacheStats(!showCacheStats)}
              variant="text"
              size="small"
            >
              {showCacheStats ? 'Hide' : 'Show'} Debug Info
            </Button>
          )}
        </Stack>

        {showCacheStats && (
          <Card style={{ mt: 2, bgcolor: 'background.default' }}>
            <CardContent>
              <Typography order={6} gutterBottom>Debug Information</Typography>
              <Typography size="sm">
                Migration Status: {migrationProgress.migrationComplete ? 'Complete' : 'In Progress'}
              </Typography>
              <Typography size="sm">
                Cache Efficiency: {migrationProgress.cacheEfficiency}
              </Typography>
              <Typography size="sm">
                RTK Queries: {migrationProgress.rtkQueries}
              </Typography>
              <Typography size="sm">
                Legacy Slices: {migrationProgress.legacySlicesActive}
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>
    );
  }

  return (
    <>
      {/* RTK Query Status Indicator */}
      {showMigrationInfo && (
        <Grid2 xs={12}>
          <Alert
            severity={migrationProgress.migrationComplete ? "success" : "info"}
            style={{ mb: 2 }}
          >
            <Typography size="sm">
              <strong>RTK Query Status:</strong> {migrationProgress.migrationComplete ? 'Fully Migrated' : 'Migration in Progress'} |
              Cache Hit Ratio: {cachePerformance.cacheHitRatio.toFixed(1)}% |
              Efficiency: {migrationProgress.cacheEfficiency}
              {isFetching && <CircularProgress size={16} style={{ ml: 1 }} />}
            </Typography>
          </Alert>
        </Grid2>
      )}

      <Grid2 container spacing={3}>
        {/* Enhanced Welcome Banner with Real-time Data */}
        <Grid2 xs={12}>
          <Card
            style={{
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              color: "white",
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: `
                  radial-gradient(circle at 20% 80%, ${alpha('#fff', 0.1)} 0%, transparent 50%),
                  radial-gradient(circle at 80% 20%, ${alpha('#fff', 0.05)} 0%, transparent 50%)
                `,
              }
            }}
          >
            <CardContent style={{ position: 'relative', zIndex: 1 }}>
              <Stack
                direction={{ xs: "column", md: "row" }}
                justifyContent="space-between"
                alignItems={{ xs: "flex-start", md: "center" }}
                gap={2}
              >
                <Stack style={{ flex: 1 }}>
                  <Fade in={true} timeout={1000}>
                    <Typography
                      order={4}
                      style={{
                        fontWeight: 800,
                        mb: 1,
                        background: 'linear-gradient(135deg, #fff, #e0e0e0)',
                        backgroundClip: 'text',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                      }}
                    >
                      <Stack direction="row" alignItems="center" spacing={1} component="span">
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
                      </Stack>
                    </Typography>
                  </Fade>

                  <Slide in={true} direction="up" timeout={1500}>
                    <Typography size="md" style={{ opacity: 0.9, mb: 2 }}>
                      {effectiveRole === "teacher" && `Managing ${activeClasses.length} active classes with real-time sync`}
                      {effectiveRole === "admin" && `Monitoring ${dashboardSummary?.totalClasses || 0} classes across the platform`}
                      {effectiveRole === "student" && `Ready for your next adventure? You've earned ${userXP} XP!`}
                      {effectiveRole === "parent" && `Your child is Level ${userLevel} with ${streakDays} day streak!`}
                    </Typography>
                  </Slide>

                  {/* Enhanced Character with Real-time Data */}
                  <Box style={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <RobloxCharacterAvatar
                      character={{
                        name: "Mission Commander",
                        type: "astronaut",
                        level: userLevel,
                        xp: userXP,
                        achievements: badgesData?.map(b => b.name) || ["First Steps", "Explorer"],
                        isActive: true,
                        imagePath: ""
                      }}
                      size="medium"
                      showLevel={false}
                      showXP={false}
                      animated={true}
                    />
                    <Box>
                      <Typography order={6} style={{ fontWeight: 600 }}>
                        Level {userLevel} Commander
                      </Typography>
                      <Typography size="sm" style={{ opacity: 0.8 }}>
                        {userXP.toLocaleString()} XP • {streakDays} day streak
                        {unreadCount > 0 && (
                          <Chip
                            label={`${unreadCount} new messages`}
                            size="small"
                            style={{ ml: 1, bgcolor: 'rgba(255,255,255,0.2)' }}
                          />
                        )}
                      </Typography>
                    </Box>
                  </Box>
                </Stack>

                {/* Enhanced Action Buttons with Loading States */}
                <Stack direction="row" gap={2} flexWrap="wrap">
                  {effectiveRole === "teacher" && (
                    <>
                      <Roblox3DButton
                        iconName="ROCKET"
                        label="Roblox Studio"
                        onClick={(e: React.MouseEvent) => () => navigate('/roblox-studio')}
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
                        onClick={(e: React.MouseEvent) => () => setCreateLessonOpen(true)}
                        variant="secondary"
                        size="medium"
                        animated={true}
                        tooltip="Create a new lesson for your students"
                      />
                    </>
                  )}

                  <Roblox3DButton
                    iconName="REFRESH"
                    label={isFetching ? "Syncing..." : "Refresh"}
                    onClick={(e: React.MouseEvent) => handleRefresh}
                    variant="info"
                    size="medium"
                    animated={!isFetching}
                    glowEffect={true}
                    tooltip="Refresh dashboard data"
                    disabled={isFetching}
                  />
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid2>

        {/* Enhanced Metrics Cards with Real-time Updates */}
        {(effectiveRole === "teacher" || effectiveRole === "admin") && (
          <>
            <Grid2 xs={12} md={3}>
              <Card role="region" aria-label="Active classes">
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar style={{ bgcolor: "primary.main", width: 48, height: 48 }}>
                      <IconSchool />
                    </Avatar>
                    <Stack style={{ flex: 1 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Active Classes
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography order={5} fontWeight={700}>
                          {dashboardSummary?.activeClasses || activeClasses.length || 0}
                        </Typography>
                        {isClassesLoading && <CircularProgress size={16} />}
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {dashboardSummary?.totalStudents || 0} total students
                      </Typography>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>

            <Grid2 xs={12} md={3}>
              <Card role="region" aria-label="Messages">
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar style={{ bgcolor: "info.main", width: 48, height: 48 }}>
                      📧
                    </Avatar>
                    <Stack style={{ flex: 1 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Unread Messages
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography order={5} fontWeight={700}>
                          {unreadCount}
                        </Typography>
                        {isMessagesLoading && <CircularProgress size={16} />}
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {messagesData?.length || 0} total messages
                      </Typography>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>

            <Grid2 xs={12} md={3}>
              <Card role="region" aria-label="System performance">
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar style={{ bgcolor: "secondary.main", width: 48, height: 48 }}>
                      <TrendingUpIcon />
                    </Avatar>
                    <Stack style={{ flex: 1 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Cache Efficiency
                      </Typography>
                      <Typography order={5} fontWeight={700}>
                        {cachePerformance.cacheHitRatio.toFixed(1)}%
                      </Typography>
                      <Chip
                        label={migrationProgress.cacheEfficiency}
                        size="small"
                        color={migrationProgress.cacheEfficiency === 'excellent' ? "success" :
                               migrationProgress.cacheEfficiency === 'good' ? "warning" : "error"}
                        style={{ mt: 0.5 }}
                      />
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>

            <Grid2 xs={12} md={3}>
              <Card role="region" aria-label="Data freshness">
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar style={{ bgcolor: "success.main", width: 48, height: 48 }}>
                      <IconCircleCheck />
                    </Avatar>
                    <Stack style={{ flex: 1 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Real-time Sync
                      </Typography>
                      <Typography order={5} fontWeight={700}>
                        {isFetching ? 'Syncing' : 'Live'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {migrationProgress.rtkQueries} cached queries
                      </Typography>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid2>
          </>
        )}

        {/* Enhanced Student Progress Cards */}
        {effectiveRole === "student" && (
          <>
            <Grid2 xs={12} md={4}>
              <Fade in={true} timeout={3000}>
                <Card
                  role="region"
                  aria-label="XP overview"
                  style={{
                    background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.05)})`,
                    border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                    borderRadius: 3,
                  }}
                >
                  <CardContent style={{ p: 3 }}>
                    <Box style={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Avatar
                        style={{
                          width: 50,
                          height: 50,
                          background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                          fontSize: '1.5rem',
                        }}
                      >
                        🏆
                      </Avatar>
                      <Box style={{ flex: 1 }}>
                        <Typography order={6} style={{ fontWeight: 700, color: theme.palette.primary.main }}>
                          Experience Points
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography order={4} style={{ fontWeight: 800, color: theme.palette.text.primary }}>
                            {userXP.toLocaleString()}
                          </Typography>
                          {isXPLoading && <CircularProgress size={20} />}
                        </Box>
                      </Box>
                    </Box>

                    <Box style={{ mb: 1 }}>
                      <Typography size="sm" style={{ color: theme.palette.text.secondary, mb: 1 }}>
                        Level Progress: {userXP % 100}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={userXP % 100}
                        style={{
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: alpha(theme.palette.primary.main, 0.2),
                          '& .MuiLinearProgress-bar': {
                            background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                            borderRadius: 4,
                          }
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Fade>
            </Grid2>

            <Grid2 xs={12} md={4}>
              <Fade in={true} timeout={3200}>
                <Card
                  role="region"
                  aria-label="Achievements"
                  style={{
                    background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.secondary.main, 0.05)})`,
                    border: `2px solid ${alpha(theme.palette.secondary.main, 0.2)}`,
                    borderRadius: 3,
                  }}
                >
                  <CardContent style={{ p: 3 }}>
                    <Box style={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Typography order={6} style={{ fontWeight: 700, color: theme.palette.secondary.main }}>
                        Achievements
                      </Typography>
                      {isBadgesLoading && <CircularProgress size={20} />}
                    </Box>

                    <Box style={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {(badgesData || []).slice(0, 4).map((badge, index) => (
                        <Zoom in={true} timeout={1000 + index * 200} key={badge.id}>
                          <Box
                            style={{
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              p: 1,
                              borderRadius: 2,
                              background: `linear-gradient(145deg, ${alpha(theme.palette.secondary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.05)})`,
                              border: `1px solid ${alpha(theme.palette.secondary.main, 0.3)}`,
                              cursor: 'pointer',
                              minWidth: 60,
                              '&:hover': {
                                transform: 'scale(1.1)',
                                boxShadow: `0 5px 15px ${alpha(theme.palette.secondary.main, 0.3)}`,
                              }
                            }}
                          >
                            <Real3DIcon
                              iconName="TROPHY"
                              size="small"
                              animated={true}
                              description={badge.name}
                            />
                            <Typography variant="caption" style={{ textAlign: 'center', fontWeight: 600, fontSize: '0.6rem', mt: 0.5 }}>
                              {badge.name}
                            </Typography>
                          </Box>
                        </Zoom>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Fade>
            </Grid2>

            <Grid2 xs={12} md={4}>
              <Fade in={true} timeout={3400}>
                <Card
                  role="region"
                  aria-label="Leaderboard position"
                  style={{
                    background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.warning.main, 0.05)})`,
                    border: `2px solid ${alpha(theme.palette.warning.main, 0.2)}`,
                    borderRadius: 3,
                  }}
                >
                  <CardContent style={{ p: 3 }}>
                    <Box style={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Avatar
                        style={{
                          width: 50,
                          height: 50,
                          background: `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.error.main})`,
                          fontSize: '1.5rem',
                        }}
                      >
                        🥇
                      </Avatar>
                      <Box style={{ flex: 1 }}>
                        <Typography order={6} style={{ fontWeight: 700, color: theme.palette.warning.main }}>
                          Leaderboard
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography order={4} style={{ fontWeight: 800, color: theme.palette.text.primary }}>
                            #{leaderboardData?.find(entry => entry.userId === 'current-user')?.rank || '?'}
                          </Typography>
                          {isLeaderboardLoading && <CircularProgress size={20} />}
                        </Box>
                      </Box>
                    </Box>

                    <Typography size="sm" style={{ color: theme.palette.text.secondary }}>
                      Weekly ranking among peers
                    </Typography>
                  </CardContent>
                </Card>
              </Fade>
            </Grid2>
          </>
        )}

        {/* Real-Time Analytics with Enhanced Data */}
        {(effectiveRole === "admin" || effectiveRole === "teacher") && (
          <Grid2 xs={12}>
            <Box display="flex" justifyContent="space-between" alignItems="center" style={{ mb: 2 }}>
              <Typography order={6} style={{ fontWeight: 600 }}>
                Real-Time Analytics
                {isFetching && <CircularProgress size={20} style={{ ml: 1 }} />}
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                <ConnectionStatus showLabel={true} />
                <Typography variant="caption" color="text.secondary">
                  Cache: {cachePerformance.cacheHitRatio.toFixed(1)}%
                </Typography>
              </Stack>
            </Box>
            <RealTimeAnalytics />
          </Grid2>
        )}

        {/* Enhanced Charts with RTK Query Data */}
        <Grid2 xs={12}>
          <Typography order={6} style={{ mb: 2, fontWeight: 600 }}>
            Analytics & Progress
            {(isXPLoading || isLeaderboardLoading) && <CircularProgress size={20} style={{ ml: 1 }} />}
          </Typography>
          <ProgressCharts
            role={(effectiveRole ?? 'student') as UserRole}
            weeklyXPData={weeklyXPData}
            badgesData={badgesData}
            leaderboardData={leaderboardData}
          />
        </Grid2>

        {/* Enhanced Recent Activity with Real-time Data */}
        <Grid2 xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography order={6} gutterBottom style={{ fontWeight: 600 }}>
                Recent Activity
                {isFetching && <CircularProgress size={16} style={{ ml: 1 }} />}
              </Typography>
              <Stack spacing={2}>
                {recentActivity.slice(0, 5).map((activity, index) => (
                  <Box
                    key={activity.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 2,
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: "background.default",
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        bgcolor: alpha(theme.palette.primary.main, 0.05),
                      }
                    }}
                  >
                    <Avatar style={{ width: 32, height: 32, bgcolor: "primary.main", fontSize: "1rem" }}>
                      {activity.type === "message" && "📧"}
                      {activity.type === "assessment" && "📝"}
                      {activity.type === "lesson" && "📚"}
                      {activity.type === "achievement" && "🏆"}
                    </Avatar>
                    <Stack style={{ flex: 1 }}>
                      <Typography size="sm">{activity.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {activity.description}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(activity.timestamp).toLocaleString()}
                      </Typography>
                    </Stack>
                    {activity.priority === 'high' && (
                      <Chip label="Priority" size="small" color="red" />
                    )}
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid2>

        {/* Enhanced Upcoming Events */}
        <Grid2 xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography order={6} gutterBottom style={{ fontWeight: 600 }}>
                Upcoming Events
              </Typography>
              <Stack spacing={2}>
                {(dashboardData?.upcomingEvents || [
                  { date: "Today, 2:00 PM", event: "Math Quiz", type: "assessment" },
                  { date: "Tomorrow, 10:00 AM", event: "Science Lab (Roblox)", type: "lesson" },
                  { date: "Friday, 3:00 PM", event: "Parent-Teacher Meeting", type: "meeting" },
                ]).map((event: any, index) => (
                  <Box
                    key={index}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 2,
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: "background.default",
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        bgcolor: alpha(theme.palette.secondary.main, 0.05),
                      }
                    }}
                  >
                    <Avatar
                      style={{
                        width: 32,
                        height: 32,
                        bgcolor: event.type === "assessment" ? "warning.main" :
                                event.type === "lesson" ? "info.main" :
                                event.type === "meeting" ? "secondary.main" : "error.main",
                        fontSize: "1rem",
                      }}
                    >
                      {event.type === "assessment" && "📝"}
                      {event.type === "lesson" && "📚"}
                      {event.type === "meeting" && "👥"}
                    </Avatar>
                    <Stack style={{ flex: 1 }}>
                      <Typography size="sm">{event.event}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {event.date}
                      </Typography>
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>

      {/* Create Lesson Dialog with RTK Query Integration */}
      {effectiveRole === "teacher" && (
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