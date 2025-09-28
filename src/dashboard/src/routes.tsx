import * as React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { DashboardHome } from "./components/pages/DashboardHome";
import Lessons from "./components/pages/Lessons";
import Assessments from "./components/pages/Assessments";
import Leaderboard from "./components/pages/Leaderboard";
import Compliance from "./components/pages/Compliance";
import Integrations from "./components/pages/Integrations";
import Messages from "./components/pages/Messages";
import Classes from "./components/pages/Classes";
import Reports from "./components/pages/Reports";
import Settings from "./components/pages/Settings";
import Missions from "./components/pages/Missions";
import Progress from "./components/pages/Progress";
import Rewards from "./components/pages/Rewards";
import Avatar from "./components/pages/Avatar";
import Schools from "./components/pages/admin/Schools";
import Users from "./components/pages/admin/Users";
import Analytics from "./components/pages/admin/Analytics";
import Play from "./components/pages/student/Play";
import { WebSocketTest } from "./components/test/WebSocketTest";
import RoleGuard from "./components/common/RoleGuard";
import { UserRole } from "./types";
import { useAppSelector } from "./store";
import TeacherRobloxDashboard from "./components/pages/TeacherRobloxDashboard";

export default function AppRoutes() {
  const role: UserRole = useAppSelector((s) => s.user.role);

  return (
    <Routes>
      <Route path="/" element={<DashboardHome role={role} />} />

      {/* Teacher Routes */}
      <Route
        path="/lessons"
        element={
          <RoleGuard allow={["Teacher", "Admin"]}>
            <Lessons />
          </RoleGuard>
        }
      />
      <Route
        path="/assessments"
        element={
          <RoleGuard allow={["Teacher", "Admin"]}>
            <Assessments />
          </RoleGuard>
        }
      />
      <Route
        path="/classes"
        element={
          <RoleGuard allow={["Teacher", "Admin"]}>
            <Classes />
          </RoleGuard>
        }
      />

      {/* Student Routes */}
      <Route
        path="/missions"
        element={
          <RoleGuard allow={["Student"]}>
            <Missions />
          </RoleGuard>
        }
      />
      <Route
        path="/rewards"
        element={
          <RoleGuard allow={["Student"]}>
            <Rewards />
          </RoleGuard>
        }
      />
      <Route
        path="/avatar"
        element={
          <RoleGuard allow={["Student"]}>
            <Avatar />
          </RoleGuard>
        }
      />
      <Route
        path="/play"
        element={
          <RoleGuard allow={["Student"]}>
            <Play />
          </RoleGuard>
        }
      />

      {/* Roblox Routes */}
      <Route
        path="/roblox/*"
        element={
          <RoleGuard allow={["Teacher", "Admin"]}>
            <TeacherRobloxDashboard />
          </RoleGuard>
        }
      />

      {/* Shared Routes */}
      <Route
        path="/leaderboard"
        element={
          <RoleGuard allow={["Student", "Teacher", "Admin"]}>
            <Leaderboard />
          </RoleGuard>
        }
      />
      <Route
        path="/progress"
        element={
          <RoleGuard allow={["Student", "Parent", "Teacher", "Admin"]}>
            <Progress />
          </RoleGuard>
        }
      />
      <Route
        path="/reports"
        element={
          <RoleGuard allow={["Parent", "Teacher", "Admin"]}>
            <Reports />
          </RoleGuard>
        }
      />

      {/* Admin Routes */}
      <Route
        path="/compliance"
        element={
          <RoleGuard allow={["Admin"]}>
            <Compliance />
          </RoleGuard>
        }
      />
      <Route
        path="/integrations"
        element={
          <RoleGuard allow={["Admin"]}>
            <Integrations />
          </RoleGuard>
        }
      />
      <Route
        path="/schools"
        element={
          <RoleGuard allow={["Admin"]}>
            <Schools />
          </RoleGuard>
        }
      />
      <Route
        path="/users"
        element={
          <RoleGuard allow={["Admin"]}>
            <Users />
          </RoleGuard>
        }
      />
      <Route
        path="/analytics"
        element={
          <RoleGuard allow={["Admin"]}>
            <Analytics />
          </RoleGuard>
        }
      />

      {/* Parent Routes */}
      <Route
        path="/messages"
        element={
          <RoleGuard allow={["Parent", "Teacher", "Admin"]}>
            <Messages />
          </RoleGuard>
        }
      />

      {/* Settings - All roles */}
      <Route path="/settings" element={<Settings />} />

      {/* Development Test Route */}
      <Route path="/websocket-test" element={<WebSocketTest />} />

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
