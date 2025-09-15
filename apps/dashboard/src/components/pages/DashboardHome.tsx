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

// Data loader
  const loadDashboardData = useCallback(async () => {
    if (!effectiveRole) {
      // No role available, nothing to load
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const data = await getDashboardOverview(effectiveRole);
      setDashboardData(data);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  }, [effectiveRole]);

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
        <Typography variant="body2">{error}</Typography>
        <Button onClick={() => window.location.reload()} variant="contained" sx={{ mt: 2 }}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <>
      <Grid2 container spacing={3}>
      {/* Welcome Banner */}
      <Grid2 xs={12}>
        <Card
          sx={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
          }}
        >
          <CardContent>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
              gap={2}
            >
              <Stack>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                  Welcome back! 👋
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  {role === "teacher" && "Review today's classes, push lessons to Roblox, and track assessments."}
                  {role === "admin" && "Monitor usage across schools, manage integrations, and review compliance."}
                  {role === "student" && "Jump into your next mission, level up, and check the leaderboard!"}
                  {role === "parent" && "See your child's progress, download reports, and message teachers."}
                </Typography>
              </Stack>
              <Stack direction="row" gap={1}>
                {role === "teacher" && (
                  <>
                    <Button 
                      variant="contained" 
                      color="secondary" 
                      startIcon={<SchoolIcon />}
                      onClick={() => setCreateLessonOpen(true)}
                    >
                      Create Lesson
                    </Button>
                    <Button 
                      variant="outlined" 
                      sx={{ color: "white", borderColor: "white" }}
                      onClick={() => navigate(ROUTES.ASSESSMENTS)}
                    >
                      View Assessments
                    </Button>
                  </>
                )}
                {role === "admin" && (
                  <>
                    <Button 
                      variant="contained" 
                      color="secondary"
                      onClick={() => navigate(ROUTES.ANALYTICS)}
                    >
                      Analytics
                    </Button>
                    <Button 
                      variant="outlined" 
                      sx={{ color: "white", borderColor: "white" }}
                      onClick={() => navigate(ROUTES.INTEGRATIONS)}
                    >
                      Manage LMS
                    </Button>
                  </>
                )}
                {role === "student" && (
                  <>
                    <Button
                      variant="contained"
                      color="secondary"
                      startIcon={<RocketLaunchIcon />}
                      onClick={handleCompleteTask}
                    >
                      Enter Roblox World
                    </Button>
                    <Button 
                      variant="outlined" 
                      sx={{ color: "white", borderColor: "white" }}
                      onClick={() => navigate(ROUTES.REWARDS)}
                    >
                      View Rewards
                    </Button>
                  </>
                )}
                {role === "parent" && (
                  <>
                    <Button 
                      variant="contained" 
                      color="secondary"
                      startIcon={<SportsEsportsIcon />}
                      onClick={() => navigate('/gameplay-replay')}
                    >
                      Watch Gameplay
                    </Button>
                    <Button 
                      variant="outlined" 
                      sx={{ color: "white", borderColor: "white" }}
                      startIcon={<AssessmentIcon />}
                      onClick={() => navigate(ROUTES.REPORTS)}
                    >
                      View Reports
                    </Button>
                  </>
                )}
                <Button 
                  variant="outlined"
                  sx={{ color: "white", borderColor: "white" }}
                  onClick={() => void loadDashboardData()}
                >
                  Refresh
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* KPI Cards */}
      {role === "student" && (
        <>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="XP overview">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "primary.main", width: 48, height: 48 }}>
                    <TrendingUpIcon />
                  </Avatar>
                  <Stack sx={{ flex: 1 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Total XP
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {xp.toLocaleString()}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={(xp % 100)}
                      aria-label={`XP progress ${xp % 100}%`}
                      sx={{ mt: 1 }}
                    />
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Level status">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "warning.main", width: 48, height: 48 }}>
                    <EmojiEventsIcon />
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Current Level
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      Level {level}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {100 - (xp % 100)} XP to next level
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Badges earned">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "info.main", width: 48, height: 48 }}>
                    <EmojiEventsIcon />
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Badges Earned
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {badgesCount}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      New this week: 2
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
          <Grid2 xs={12} md={3}>
            <Card role="region" aria-label="Streak days">
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Avatar sx={{ bgcolor: "secondary.main", width: 48, height: 48 }}>
                    🔥
                  </Avatar>
                  <Stack>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Streak Days
                    </Typography>
                    <Typography variant="h5" fontWeight={700}>
                      {streakDays}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Keep it up!
                    </Typography>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
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
