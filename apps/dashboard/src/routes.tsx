import { Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import { CircularProgress, Box } from "@mui/material";
import RoleGuard from "./components/common/RoleGuard";
import { useAppSelector } from "./store";

// Lazy load components for code splitting
const DashboardHome = lazy(() => import("./components/pages/DashboardHome"));
const Lessons = lazy(() => import("./components/pages/Lessons"));
const Assessments = lazy(() => import("./components/pages/Assessments"));
const Leaderboard = lazy(() => import("./components/pages/Leaderboard"));
const Compliance = lazy(() => import("./components/pages/Compliance"));
const Integrations = lazy(() => import("./components/pages/Integrations"));
const Messages = lazy(() => import("./components/pages/Messages"));
const Classes = lazy(() => import("./components/pages/Classes"));
// const ClassDetails = lazy(() => import("./components/pages/ClassDetails"));
const ClassDetail = lazy(() => import("./components/ClassDetail/ClassDetail"));
const Reports = lazy(() => import("./components/pages/Reports"));
const Settings = lazy(() => import("./components/pages/Settings"));
const Missions = lazy(() => import("./components/pages/Missions"));
const Progress = lazy(() => import("./components/pages/Progress"));
const Rewards = lazy(() => import("./components/pages/Rewards"));
const Avatar = lazy(() => import("./components/pages/Avatar"));
const GameplayReplay = lazy(() => import("./components/pages/GameplayReplay"));
const Schools = lazy(() => import("./components/pages/admin/Schools"));
const Users = lazy(() => import("./components/pages/admin/Users"));
const Analytics = lazy(() => import("./components/pages/admin/Analytics"));
const Play = lazy(() => import("./components/pages/student/Play"));
const WebSocketTest = lazy(() => import("./components/test/WebSocketTest"));
const WebSocketDemo = lazy(() => import("./components/test/WebSocketDemo"));
const TeacherRobloxDashboard = lazy(() => import("./components/pages/TeacherRobloxDashboard"));
const EnvironmentCreator = lazy(() => import("./components/roblox/EnvironmentCreator"));
const EnvironmentPreviewPage = lazy(() => import("./components/roblox/EnvironmentPreviewPage"));
const RobloxStudioPage = lazy(() => import("./components/pages/RobloxStudioPage"));
const AgentDashboard = lazy(() => import("./pages/AgentDashboard"));

// Loading component for Suspense fallback
const LoadingFallback = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="400px"
    flexDirection="column"
    gap={2}
  >
    <CircularProgress size={40} />
    <Box component="span" sx={{ color: 'text.secondary', fontSize: '0.875rem' }}>
      Loading...
    </Box>
  </Box>
);

export default function AppRoutes() {
  const role = useAppSelector((s) => s.user.role);

  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
      <Route path="/" element={<DashboardHome role={role} />} />

      {/* Teacher Routes */}
      <Route
        path="/lessons"
        element={
          <RoleGuard allow={["teacher", "admin"]}>
            <Lessons />
          </RoleGuard>
        }
      />
      <Route
        path="/assessments"
        element={
          <RoleGuard allow={["teacher", "admin"]}>
            <Assessments />
          </RoleGuard>
        }
      />
      <Route
        path="/classes"
        element={
          <RoleGuard allow={["teacher", "admin"]}>
            <Classes />
          </RoleGuard>
        }
      />
      <Route
        path="/classes/:classId"
        element={
          <RoleGuard allow={["teacher", "admin", "student", "parent"]}>
            <ClassDetail />
          </RoleGuard>
        }
      />

      {/* Student Routes */}
      <Route
        path="/missions"
        element={
          <RoleGuard allow={["student"]}>
            <Missions />
          </RoleGuard>
        }
      />
      <Route
        path="/rewards"
        element={
          <RoleGuard allow={["student"]}>
            <Rewards />
          </RoleGuard>
        }
      />
      <Route
        path="/avatar"
        element={
          <RoleGuard allow={["student"]}>
            <Avatar />
          </RoleGuard>
        }
      />
      <Route
        path="/play"
        element={
          <RoleGuard allow={["student"]}>
            <Play />
          </RoleGuard>
        }
      />

      {/* Roblox Routes */}
      <Route
        path="/roblox/*"
        element={
          <RoleGuard allow={["teacher", "admin"]}>
            <TeacherRobloxDashboard />
          </RoleGuard>
        }
      />
      <Route
        path="/environment-preview/:environmentId"
        element={
          <RoleGuard allow={["teacher", "admin", "student"]}>
            <EnvironmentPreviewPage />
          </RoleGuard>
        }
      />

      {/* Shared Routes */}
      <Route
        path="/leaderboard"
        element={
          <RoleGuard allow={["student", "teacher", "admin"]}>
            <Leaderboard />
          </RoleGuard>
        }
      />
      <Route
        path="/progress"
        element={
          <RoleGuard allow={["student", "parent", "teacher", "admin"]}>
            <Progress />
          </RoleGuard>
        }
      />
      <Route
        path="/reports"
        element={
          <RoleGuard allow={["parent", "teacher", "admin"]}>
            <Reports />
          </RoleGuard>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/compliance"
        element={
          <RoleGuard allow={["admin"]}>
            <Compliance />
          </RoleGuard>
        }
      />
      <Route
        path="/integrations"
        element={
          <RoleGuard allow={["admin"]}>
            <Integrations />
          </RoleGuard>
        }
      />
      <Route
        path="/schools"
        element={
          <RoleGuard allow={["admin"]}>
            <Schools />
          </RoleGuard>
        }
      />
      <Route
        path="/users"
        element={
          <RoleGuard allow={["admin"]}>
            <Users />
          </RoleGuard>
        }
      />
      <Route
        path="/analytics"
        element={
          <RoleGuard allow={["admin"]}>
            <Analytics />
          </RoleGuard>
        }
      />
      <Route
        path="/agents"
        element={
          <RoleGuard allow={["admin"]}>
            <AgentDashboard />
          </RoleGuard>
        }
      />

      {/* Parent Routes */}
      <Route
        path="/messages"
        element={
          <RoleGuard allow={["parent", "teacher", "admin"]}>
            <Messages />
          </RoleGuard>
        }
      />
      <Route
        path="/gameplay-replay"
        element={
          <RoleGuard allow={["parent", "teacher", "admin"]}>
            <GameplayReplay />
          </RoleGuard>
        }
      />

      {/* Settings - All roles */}
      <Route path="/settings" element={<Settings />} />

      {/* Development Test Routes */}
      <Route path="/websocket-test" element={<WebSocketTest />} />
      <Route path="/websocket-demo" element={<WebSocketDemo />} />

      {/* Roblox Environment Creation */}
      <Route
        path="/roblox/create-environment"
        element={
          <RoleGuard allow={["teacher", "admin"]}>
            <EnvironmentCreator />
          </RoleGuard>
        }
      />

      {/* Roblox Studio Integration Page */}
      <Route
        path="/roblox-studio"
        element={
          <RoleGuard allow={["teacher", "admin"]}>
            <RobloxStudioPage />
          </RoleGuard>
        }
      />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
