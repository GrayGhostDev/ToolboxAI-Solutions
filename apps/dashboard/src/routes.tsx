import { Routes, Route, Navigate } from "react-router-dom";
import { DashboardHome } from "./components/pages/DashboardHome";
import Lessons from "./components/pages/Lessons";
import Assessments from "./components/pages/Assessments";
import Leaderboard from "./components/pages/Leaderboard";
import Compliance from "./components/pages/Compliance";
import Integrations from "./components/pages/Integrations";
import Messages from "./components/pages/Messages";
import Classes from "./components/pages/Classes";
import ClassDetails from "./components/pages/ClassDetails";
import Reports from "./components/pages/Reports";
import Settings from "./components/pages/Settings";
import Missions from "./components/pages/Missions";
import Progress from "./components/pages/Progress";
import Rewards from "./components/pages/Rewards";
import Avatar from "./components/pages/Avatar";
import GameplayReplay from "./components/pages/GameplayReplay";
import Schools from "./components/pages/admin/Schools";
import Users from "./components/pages/admin/Users";
import Analytics from "./components/pages/admin/Analytics";
import Play from "./components/pages/student/Play";
import { WebSocketTest } from "./components/test/WebSocketTest";
import WebSocketDemo from "./components/test/WebSocketDemo";
import RoleGuard from "./components/common/RoleGuard";
import { useAppSelector } from "./store";
import TeacherRobloxDashboard from "./components/pages/TeacherRobloxDashboard";
import EnvironmentCreator from "./components/roblox/EnvironmentCreator";
import EnvironmentPreviewPage from "./components/roblox/EnvironmentPreviewPage";
import RobloxStudioPage from "./components/pages/RobloxStudioPage";

export default function AppRoutes() {
  const role = useAppSelector((s) => s.user.role);

  return (
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
        path="/classes/:id"
        element={
          <RoleGuard allow={["teacher", "admin", "student", "parent"]}>
            <ClassDetails />
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
  );
}
