import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Grid2 from "@mui/material/Unstable_Grid2";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import LinearProgress from "@mui/material/LinearProgress";
import Avatar from "@mui/material/Avatar";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import RefreshIcon from "@mui/icons-material/Refresh";
import { UserRole } from "../../types";
import { ProgressCharts } from "../widgets/ProgressCharts";
import { useAppSelector, useAppDispatch } from "../../store";
import { addXP } from "../../store/slices/gamificationSlice";
import { addNotification } from "../../store/slices/uiSlice";
import { getDashboardOverview } from "../../services/api";
import { DashboardOverview } from "../../types/api";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";
import SchoolIcon from "@mui/icons-material/School";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import AssessmentIcon from "@mui/icons-material/Assessment";
import { ROUTES } from "../../config/routes";
import CreateLessonDialog from "../dialogs/CreateLessonDialog";
import RealTimeAnalytics from "../widgets/RealTimeAnalytics";
import ConnectionStatus from "../widgets/ConnectionStatus";
// Roblox-themed components
import RobloxCharacterAvatar from "../roblox/RobloxCharacterAvatar";
import Roblox3DIcon from "../roblox/Roblox3DIcon";
import { Roblox3DButton } from "../roblox/Roblox3DButton";
import { Roblox3DTabs } from "../roblox/Roblox3DTabs";
import { Roblox3DNavigation } from "../roblox/Roblox3DNavigation";
import { RobloxProgressBar } from "../roblox/RobloxProgressBar";
import { RobloxAchievementBadge } from "../roblox/RobloxAchievementBadge";
import { useTheme, alpha, Fade, Zoom, Slide } from "@mui/material";

export function DashboardHome({ role }: { role?: UserRole }) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const xp = useAppSelector((s) => s.gamification?.xp ?? 0);
  const level = useAppSelector((s) => s.gamification?.level ?? 1);
  const streakDays = useAppSelector((s) => s.gamification?.streakDays ?? 0);
  const badgesCount = useAppSelector((s) => (s.gamification?.badges ? s.gamification.badges.length : 0));
  const storeRole = useAppSelector((s) => (s as any).user?.role ?? (s as any).user?.currentUser?.role ?? null);
  const effectiveRole = (role ?? storeRole) as UserRole | null;
  const userXP = useAppSelector((s) => (s as any).user?.userId) ? xp : 0;

  const [dashboardData, setDashboardData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createLessonOpen, setCreateLessonOpen] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

// Data loader with retry mechanism and fallback
  const loadDashboardData = useCallback(async (isRetry = false) => {
    if (!effectiveRole) {
      // No role available, nothing to load
      setLoading(false);
      return;
    }
    
    try {
      if (!isRetry) {
        setLoading(true);
        setError(null);
        setRetryCount(0);
      }
      
      const data = await getDashboardOverview(effectiveRole);
      setDashboardData(data);
      setRetryCount(0); // Reset retry count on success
    } catch (err: any) {
      console.error("Dashboard data load error:", err);
      
      // After 3 failed attempts, show fallback data instead of infinite retries
      if (retryCount >= 2) {
        console.log("Using fallback dashboard data due to repeated failures");
        setDashboardData({
          role: effectiveRole,
          metrics: {
            totalStudents: 0,
            activeClasses: 0,
            averageProgress: 0
          },
          recentActivity: [],
          notifications: [],
          kpis: {
            totalStudents: 0,
            activeSessions: 0,
            completedLessons: 0,
            averageScore: 0,
            progressChange: 0
          }
        });
        setError('Using offline mode - some features may be limited. Check your connection and refresh to sync with server.');
        setLoading(false);
        return;
      }
      
      // Provide more specific error messages
      if (err && typeof err === 'object' && 'code' in err && err.code === 'ECONNABORTED') {
        if (retryCount < 2 && !isRetry) {
          // Retry for timeout errors (only on initial load, not on retries)
          setRetryCount(prev => prev + 1);
          setTimeout(() => {
            loadDashboardData(true);
          }, 2000 * (retryCount + 1)); // Exponential backoff
          setError(`Connection timeout. Retrying... (${retryCount + 1}/3)`);
          return;
        } else {
          setError('Dashboard data is taking longer than expected. Please check your connection and try refreshing the page.');
        }
      } else if (err && typeof err === 'object' && 'response' in err) {
        const status = err.response?.status;
        if (status === 401) {
          setError('Authentication expired. Please refresh the page and log in again.');
        } else if (status === 500) {
          if (retryCount < 1 && !isRetry) {
            // Retry once for server errors (only on initial load, not on retries)
            setRetryCount(prev => prev + 1);
            setTimeout(() => {
              loadDashboardData(true);
            }, 3000);
            setError('Server error. Retrying...');
            return;
          } else {
            setError('Server error. Please try again in a moment.');
          }
        } else if (status === 404) {
          setError('Dashboard endpoint not found. Please contact support.');
        } else {
          setError(err.message || "Failed to load dashboard data");
        }
      } else {
        setError(err.message || "Failed to load dashboard data");
      }
    } finally {
      if (!isRetry) {
        setLoading(false);
      }
    }
  }, [effectiveRole, retryCount]);

  // Load on mount or role change
  useEffect(() => {
    void loadDashboardData();
  }, [loadDashboardData]);

  // Navigate to Play page for students
  const handleCompleteTask = () => {
    if (effectiveRole === 'student') {
      navigate('/play');
    } else {
      dispatch(addXP({ amount: 25, reason: "Completed daily task", source: "achievement" }));
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Typography color="error" variant="h6">Error loading dashboard</Typography>
        <Typography variant="body2" sx={{ mb: 2 }}>{error}</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            onClick={() => loadDashboardData()}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <RefreshIcon />}
          >
            {loading ? 'Retrying...' : 'Retry'}
          </Button>
          <Button
            onClick={() => window.location.reload()}
            variant="outlined"
          >
            Refresh Page
          </Button>
        </Stack>
      </Box>
    );
  }

  const theme = useTheme();

  return (
    <>
      <Grid2 container spacing={3}>
      {/* Roblox-themed Welcome Banner */}
      <Grid2 xs={12}>
        <Card
          sx={{
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
              animation: 'float 20s ease-in-out infinite',
              '@keyframes float': {
                '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
                '50%': { transform: 'translateY(-20px) rotate(180deg)' }
              }
            }
          }}
        >
          <CardContent sx={{ position: 'relative', zIndex: 1 }}>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
              gap={2}
            >
              <Stack sx={{ flex: 1 }}>
                <Fade in={true} timeout={1000}>
                  <Typography 
                    variant="h4" 
                    sx={{ 
                      fontWeight: 800, 
                      mb: 1,
                      background: 'linear-gradient(135deg, #fff, #e0e0e0)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                    }}
                  >
                    🚀 Welcome to Space Station! 👋
                  </Typography>
                </Fade>
                <Slide in={true} direction="up" timeout={1500}>
                  <Typography variant="body1" sx={{ opacity: 0.9, mb: 2 }}>
                    {role === "teacher" && "Review today's classes, push lessons to Roblox, and track assessments."}
                    {role === "admin" && "Monitor usage across schools, manage integrations, and review compliance."}
                    {role === "student" && "Jump into your next mission, level up, and check the leaderboard!"}
                    {role === "parent" && "See your child's progress, download reports, and message teachers."}
                  </Typography>
                </Slide>
                
                {/* Character Avatar */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <RobloxCharacterAvatar
                    character={{
                      name: 'Astro Explorer',
                      type: 'astronaut',
                      level: level,
                      xp: userXP,
                      achievements: ['Space Walker', 'Quiz Master'],
                      isActive: true,
                      imagePath: '/images/characters/PNG/Astronauto (variation)/01.png'
                    }}
                    size="medium"
                    animated={true}
                  />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Level {level} Explorer
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      {userXP} XP • {streakDays} day streak
                    </Typography>
                  </Box>
                </Box>
              </Stack>
              <Stack direction="row" gap={2} flexWrap="wrap">
                {role === "teacher" && (
                  <>
                    <Roblox3DButton
                      iconName="OPEN_BOOK"
                      label="Create Lesson"
                      onClick={() => setCreateLessonOpen(true)}
                      variant="primary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="Create a new lesson for your students"
                    />
                    <Roblox3DButton
                      iconName="ASSESSMENT"
                      label="View Assessments"
                      onClick={() => navigate(ROUTES.ASSESSMENTS)}
                      variant="secondary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="Review student assessments and progress"
                    />
                  </>
                )}
                {role === "admin" && (
                  <>
                    <Roblox3DButton
                      iconName="LIGHT_BULB"
                      label="Analytics"
                      onClick={() => navigate(ROUTES.ANALYTICS)}
                      variant="primary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="View system analytics and reports"
                    />
                    <Roblox3DButton
                      iconName="SETTINGS"
                      label="Manage LMS"
                      onClick={() => navigate(ROUTES.INTEGRATIONS)}
                      variant="secondary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="Manage learning management system"
                    />
                  </>
                )}
                {role === "student" && (
                  <>
                    <Roblox3DButton
                      iconName="ROCKET"
                      label="Enter Roblox World"
                      onClick={handleCompleteTask}
                      variant="primary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="Jump into your Roblox learning world"
                    />
                    <Roblox3DButton
                      iconName="TROPHY"
                      label="View Rewards"
                      onClick={() => navigate(ROUTES.REWARDS)}
                      variant="secondary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="Check your achievements and rewards"
                    />
                  </>
                )}
                {role === "parent" && (
                  <>
                    <Roblox3DButton
                      iconName="SPORTS_ESPORTS"
                      label="Watch Gameplay"
                      onClick={() => navigate('/gameplay-replay')}
                      variant="primary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="Watch your child's learning gameplay"
                    />
                    <Roblox3DButton
                      iconName="ASSESSMENT"
                      label="View Reports"
                      onClick={() => navigate(ROUTES.REPORTS)}
                      variant="secondary"
                      size="medium"
                      animated={true}
                      glowEffect={true}
                      tooltip="View detailed progress reports"
                    />
                  </>
                )}
                <Roblox3DButton
                  iconName="REFRESH"
                  label="Refresh"
                  onClick={() => void loadDashboardData()}
                  variant="info"
                  size="medium"
                  animated={true}
                  glowEffect={true}
                  tooltip="Refresh dashboard data"
                />
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* 3D Educational Tools Section */}
      <Grid2 xs={12}>
        <Fade in={true} timeout={2000}>
          <Card
            sx={{
              background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.05)})`,
              border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
              borderRadius: 3,
              overflow: 'hidden'
            }}
          >
            <CardContent sx={{ p: 4 }}>
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  mb: 3,
                  textAlign: 'center',
                  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                🎮 Your Learning Tools
              </Typography>
              
              <Grid2 container spacing={3} justifyContent="center">
                {[
                  {
                    name: 'ABC_CUBE',
                    type: 'education' as const,
                    category: 'Language',
                    level: 3,
                    isUnlocked: true,
                    description: 'Learn the alphabet with interactive 3D cubes'
                  },
                  {
                    name: 'MATH_BOARD',
                    type: 'education' as const,
                    category: 'Mathematics',
                    level: 2,
                    isUnlocked: true,
                    description: 'Solve math problems on the interactive board'
                  },
                  {
                    name: 'SPACE_QUIZ',
                    type: 'education' as const,
                    category: 'Science',
                    level: 4,
                    isUnlocked: true,
                    description: 'Test your knowledge about space and planets'
                  },
                  {
                    name: 'SPORTS_CHALLENGE',
                    type: 'gaming' as const,
                    category: 'Physical Education',
                    level: 1,
                    isUnlocked: true,
                    description: 'Complete physical challenges and sports activities'
                  },
                  {
                    name: 'ART_STUDIO',
                    type: 'tool' as const,
                    category: 'Creative Arts',
                    level: 2,
                    isUnlocked: true,
                    description: 'Create digital art with brushes and colors'
                  },
                  {
                    name: 'ACHIEVEMENT_HALL',
                    type: 'achievement' as const,
                    category: 'Recognition',
                    level: 5,
                    isUnlocked: true,
                    description: 'View all your earned achievements and badges'
                  }
                ].map((tool, index) => (
                  <Grid2 xs={6} sm={4} md={2} key={index}>
                    <Zoom in={true} timeout={2000 + index * 200}>
                      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Roblox3DIcon
                          icon={tool}
                          size="large"
                          animated={true}
                          onClick={() => console.log(`Clicked ${tool.name}`)}
                        />
                      </Box>
                    </Zoom>
                  </Grid2>
                ))}
              </Grid2>
            </CardContent>
          </Card>
        </Fade>
      </Grid2>

      {/* 3D Navigation Section */}
      <Grid2 xs={12}>
        <Fade in={true} timeout={2500}>
          <Roblox3DNavigation
            items={[
              {
                id: 'dashboard',
                label: 'Dashboard',
                iconName: 'LAMP',
                path: '/dashboard',
                tooltip: 'Main dashboard overview'
              },
              {
                id: 'lessons',
                label: 'Lessons',
                iconName: 'OPEN_BOOK',
                path: '/lessons',
                badge: 3,
                tooltip: 'View and manage lessons'
              },
              {
                id: 'assessments',
                label: 'Assessments',
                iconName: 'ASSESSMENT',
                path: '/assessments',
                tooltip: 'Take and review assessments'
              },
              {
                id: 'rewards',
                label: 'Rewards',
                iconName: 'TROPHY',
                path: '/rewards',
                badge: 5,
                tooltip: 'View achievements and rewards'
              },
              {
                id: 'profile',
                label: 'Profile',
                iconName: 'BADGE',
                path: '/profile',
                tooltip: 'Manage your profile'
              }
            ]}
            onItemClick={(item) => {
              if (item.path) {
                navigate(item.path);
              }
            }}
            orientation="horizontal"
            variant="buttons"
            size="medium"
            animated={true}
            glowEffect={true}
            showLabels={true}
            compact={false}
          />
        </Fade>
      </Grid2>

      {/* 3D Progress and Achievement Cards */}
      {role === "student" && (
        <>
          <Grid2 xs={12} md={4}>
            <Fade in={true} timeout={3000}>
              <Card 
                role="region" 
                aria-label="XP overview"
                sx={{
                  background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.primary.main, 0.05)})`,
                  border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  borderRadius: 3,
                  overflow: 'hidden'
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Roblox3DIcon
                      icon={{
                        name: 'TROPHY',
                        type: 'achievement',
                        category: 'XP',
                        level: level,
                        isUnlocked: true,
                        description: 'Experience Points'
                      }}
                      size="medium"
                      animated={true}
                    />
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
                        Experience Points
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 800, color: theme.palette.text.primary }}>
                        {xp.toLocaleString()}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <RobloxProgressBar
                    current={xp % 100}
                    max={100}
                    label="Level Progress"
                    showPercentage={true}
                    animated={true}
                    color="primary"
                    size="medium"
                  />
                </CardContent>
              </Card>
            </Fade>
          </Grid2>
          <Grid2 xs={12} md={4}>
            <Fade in={true} timeout={3200}>
              <Card 
                role="region" 
                aria-label="Level status"
                sx={{
                  background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.warning.main, 0.05)})`,
                  border: `2px solid ${alpha(theme.palette.warning.main, 0.2)}`,
                  borderRadius: 3,
                  overflow: 'hidden'
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Roblox3DIcon
                      icon={{
                        name: 'STAR',
                        type: 'achievement',
                        category: 'Level',
                        level: level,
                        isUnlocked: true,
                        description: 'Current Level'
                      }}
                      size="medium"
                      animated={true}
                    />
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 700, color: theme.palette.warning.main }}>
                        Current Level
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 800, color: theme.palette.text.primary }}>
                        Level {level}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary, mb: 1 }}>
                    {100 - (xp % 100)} XP to next level
                  </Typography>
                  
                  <RobloxProgressBar
                    current={100 - (xp % 100)}
                    max={100}
                    label="Next Level"
                    showPercentage={true}
                    animated={true}
                    color="warning"
                    size="small"
                  />
                </CardContent>
              </Card>
            </Fade>
          </Grid2>
          
          <Grid2 xs={12} md={4}>
            <Fade in={true} timeout={3400}>
              <Card 
                role="region" 
                aria-label="Achievements"
                sx={{
                  background: `linear-gradient(145deg, ${theme.palette.background.paper}, ${alpha(theme.palette.secondary.main, 0.05)})`,
                  border: `2px solid ${alpha(theme.palette.secondary.main, 0.2)}`,
                  borderRadius: 3,
                  overflow: 'hidden'
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: theme.palette.secondary.main, mb: 2 }}>
                    Recent Achievements
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    {[
                      { id: '1', name: 'Space Walker', description: 'Completed first mission', rarity: 'common' as const, unlocked: true },
                      { id: '2', name: 'Quiz Master', description: 'Scored 100% on quiz', rarity: 'rare' as const, unlocked: true },
                      { id: '3', name: 'Streak Keeper', description: '7 day learning streak', rarity: 'epic' as const, unlocked: true },
                      { id: '4', name: 'Level Up', description: 'Reached level 5', rarity: 'legendary' as const, unlocked: false },
                    ].map((achievement) => (
                      <RobloxAchievementBadge
                        key={achievement.id}
                        achievement={achievement}
                        size="small"
                        animated={true}
                        onClick={(achievement) => console.log('Achievement clicked:', achievement)}
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Fade>
          </Grid2>
        </>
      )}

      {(role === "teacher" || role === "admin") && (
        <>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Active classes">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "primary.main", width: 48, height: 48 }}>
                    <SchoolIcon />
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Active Classes
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.kpis?.activeClasses || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dashboardData?.kpis?.totalStudents || 0} total students
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Lessons scheduled">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "info.main", width: 48, height: 48 }}>
                    📚
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Today's Lessons
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.kpis?.todaysLessons || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dashboardData?.kpis?.pendingAssessments || 0} assessments due
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Average progress">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "secondary.main", width: 48, height: 48 }}>
                    <TrendingUpIcon />
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Avg. Progress
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.kpis?.averageProgress || 0}%
                    </Typography>
                    <Chip
                      label={`${dashboardData?.kpis?.progressChange || 0}% this week`}
                      size="small"
                      color={((dashboardData?.kpis?.progressChange || 0) >= 0) ? "success" : "error"}
                      sx={{ mt: 0.5 }}
                    />
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Compliance status">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "success.main", width: 48, height: 48 }}>
                    <CheckCircleIcon />
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Compliance
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.compliance?.status || "Unknown"}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dashboardData?.compliance?.pendingAlerts || 0} pending alerts
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
        </>
      )}

      {role === "parent" && (
        <>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Child's XP">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "primary.main", width: 48, height: 48 }}>
                    <TrendingUpIcon />
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Child's XP
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.studentData?.xp || userXP}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Level {Math.floor((dashboardData?.studentData?.xp || userXP) / 100) + 1}
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Overall progress">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "secondary.main", width: 48, height: 48 }}>
                    📊
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Overall Progress
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.studentData?.overallProgress || 0}%
                    </Typography>
                    <Chip
                      label={dashboardData?.studentData?.performanceRating || "Average"}
                      size="small"
                      color="success"
                      sx={{ mt: 0.5 }}
                    />
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Assignments completed">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "info.main", width: 48, height: 48 }}>
                    <CheckCircleIcon />
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Assignments
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.studentData?.completedAssignments || 0}/{dashboardData?.studentData?.totalAssignments || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {(dashboardData?.studentData?.totalAssignments || 0) - (dashboardData?.studentData?.completedAssignments || 0)} pending
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Last active">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "success.main", width: 48, height: 48 }}>
                    ✅
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Last Active
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {dashboardData?.studentData?.lastActive ? new Date(dashboardData.studentData.lastActive).toLocaleDateString() : "Today"}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dashboardData?.studentData?.lastActive ? new Date(dashboardData.studentData.lastActive).toLocaleTimeString() : "Recently"}
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
        </>
      )}

      {/* Real-Time Analytics for Admin and Teacher */}
      {(role === "admin" || role === "teacher") && (
        <Grid2 xs={12}>
          <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Real-Time Analytics
            </Typography>
            <ConnectionStatus showLabel={true} />
          </Box>
          <RealTimeAnalytics />
        </Grid2>
      )}

      {/* Charts Section */}
      <Grid2 xs={12}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Analytics & Progress
        </Typography>
        <ProgressCharts role={(effectiveRole ?? 'student') as UserRole} />
      </Grid2>

      {/* Recent Activity */}
      <Grid2 xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Recent Activity
            </Typography>
            <Stack spacing={2}>
              {(dashboardData?.recentActivity || [
                { time: "2 hours ago", action: "Completed Math Lesson", type: "success" },
                { time: "5 hours ago", action: "Earned 'Problem Solver' badge", type: "achievement" },
                { time: "Yesterday", action: "Submitted Science Assignment", type: "info" },
                { time: "2 days ago", action: "Joined Roblox Chemistry Lab", type: "game" },
              ]).map((activity: any, index) => (
                <Box
                  key={index}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: "background.default",
                  }}
                >
                  <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main", fontSize: "1rem" }}>
                    {activity.type === "success" && "✓"}
                    {activity.type === "achievement" && "🏆"}
                    {activity.type === "info" && "📝"}
                    {activity.type === "game" && "🎮"}
                  </Avatar>
                  <Stack sx={{ flex: 1 }}>
                    <Typography variant="body2">{activity.action}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {activity.time}
                    </Typography>
                  </Stack>
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Upcoming Events */}
      <Grid2 xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Upcoming Events
            </Typography>
            <Stack spacing={2}>
              {(dashboardData?.upcomingEvents || [
                { date: "Today, 2:00 PM", event: "Math Quiz", type: "assessment" },
                { date: "Tomorrow, 10:00 AM", event: "Science Lab (Roblox)", type: "lesson" },
                { date: "Friday, 3:00 PM", event: "Parent-Teacher Meeting", type: "meeting" },
                { date: "Next Monday", event: "History Project Due", type: "deadline" },
              ]).map((event: any, index) => (
                <Box
                  key={index}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: "background.default",
                  }}
                >
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor:
                        event.type === "assessment"
                          ? "warning.main"
                          : event.type === "lesson"
                          ? "info.main"
                          : event.type === "meeting"
                          ? "secondary.main"
                          : "error.main",
                      fontSize: "1rem",
                    }}
                  >
                    {event.type === "assessment" && "📝"}
                    {event.type === "lesson" && "📚"}
                    {event.type === "meeting" && "👥"}
                    {event.type === "deadline" && "⏰"}
                  </Avatar>
                  <Stack sx={{ flex: 1 }}>
                    <Typography variant="body2">{event.event}</Typography>
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

      {/* Create Lesson Dialog for Teachers */}
      {role === "teacher" && (
        <CreateLessonDialog
          open={createLessonOpen}
          onClose={() => setCreateLessonOpen(false)}
          onSuccess={() => {
            setCreateLessonOpen(false);
            dispatch(
              addNotification({
                type: "success",
                message: "Lesson created successfully!",
              })
            );
          }}
        />
      )}
    </>
  );
}

export default DashboardHome;
