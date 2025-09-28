import { Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import RoleGuard from "./components/common/RoleGuard";
import { useAppSelector } from "./store";
import ProgressiveEnhancement from "./components/performance/ProgressiveEnhancement";
import { PerformanceSkeleton } from "./components/atomic/atoms/PerformanceSkeleton";

// Lazy load components with performance-aware loading
// High priority components (frequently used)
const DashboardHome = lazy(() => import("./components/pages/DashboardHome"));
const Settings = lazy(() => import("./components/pages/Settings"));

// Medium priority components (teacher/admin features)
const Lessons = lazy(() => import("./components/pages/Lessons"));
const Assessments = lazy(() => import("./components/pages/Assessments"));
const Classes = lazy(() => import("./components/pages/Classes"));
const ClassDetail = lazy(() => import("./components/ClassDetail/ClassDetail"));
const Messages = lazy(() => import("./components/pages/Messages"));
const Reports = lazy(() => import("./components/pages/Reports"));

// Low priority components (less frequently used)
const Leaderboard = lazy(() =>
  import("./components/pages/Leaderboard").then(module => ({
    default: module.default
  }))
);
const Compliance = lazy(() =>
  import("./components/pages/Compliance").then(module => ({
    default: module.default
  }))
);
const Integrations = lazy(() =>
  import("./components/pages/Integrations").then(module => ({
    default: module.default
  }))
);

// Student-specific components
const Missions = lazy(() => import("./components/pages/Missions"));
const Progress = lazy(() => import("./components/pages/Progress"));
const Rewards = lazy(() => import("./components/pages/Rewards"));
const Avatar = lazy(() => import("./components/pages/Avatar"));
const Play = lazy(() => import("./components/pages/student/Play"));

// Heavy/complex components (3D, charts, admin)
const GameplayReplay = lazy(() =>
  import("./components/pages/GameplayReplay").then(module => ({
    default: module.default
  }))
);
const Schools = lazy(() =>
  import("./components/pages/admin/Schools").then(module => ({
    default: module.default
  }))
);
const Users = lazy(() =>
  import("./components/pages/admin/Users").then(module => ({
    default: module.default
  }))
);
const Analytics = lazy(() =>
  import("./components/pages/admin/Analytics").then(module => ({
    default: module.default
  }))
);

// 3D and Roblox components (heaviest)
const TeacherRobloxDashboard = lazy(() =>
  import("./components/pages/TeacherRobloxDashboard")
);
const EnvironmentCreator = lazy(() =>
  import("./components/roblox/EnvironmentCreator").then(module => ({
    default: module.default
  }))
);
const EnvironmentPreviewPage = lazy(() =>
  import("./components/roblox/EnvironmentPreviewPage").then(module => ({
    default: module.default
  }))
);
const RobloxStudioPage = lazy(() =>
  import("./components/pages/RobloxStudioPage").then(module => ({
    default: module.default
  }))
);

// Development/test components
const WebSocketTest = lazy(() =>
  import("./components/test/WebSocketTest").then(module => ({
    default: module.default
  }))
);
const WebSocketDemo = lazy(() =>
  import("./components/test/WebSocketDemo").then(module => ({
    default: module.default
  }))
);
const HealthCheck = lazy(() => import("./pages/Health"));
// MigrationDemo removed - not needed in production
const AgentDashboard = lazy(() =>
  import("./pages/AgentDashboard").then(module => ({
    default: module.default
  }))
);
const GPT4MigrationDashboard = lazy(() =>
  import("./components/pages/GPT4MigrationDashboard").then(module => ({
    default: module.default
  }))
);

// Observability components (admin-only)
const ObservabilityDashboard = lazy(() =>
  import("./components/observability/ObservabilityDashboard").then(module => ({
    default: module.default
  }))
);

// Enhanced loading components for different scenarios
const LoadingFallback = ({ variant = 'dashboard' }: { variant?: 'dashboard' | 'card' | 'list' | 'form' }) => (
  <PerformanceSkeleton variant={variant} animate={true} />
);

// Performance-aware route wrapper
const PerformanceRoute = ({
  children,
  priority = 'medium',
  skeletonVariant = 'dashboard'
}: {
  children: React.ReactNode;
  priority?: 'high' | 'medium' | 'low';
  skeletonVariant?: 'dashboard' | 'card' | 'list' | 'chart' | 'navigation' | 'form';
}) => (
  <ProgressiveEnhancement
    priority={priority}
    skeletonVariant={skeletonVariant}
    enableIntersectionObserver={priority !== 'high'}
  >
    {children}
  </ProgressiveEnhancement>
);

export default function AppRoutes() {
  const role = useAppSelector((s) => s.user.role);

  return (
    <Suspense fallback={<LoadingFallback variant="dashboard" />}>
      <Routes>
      {/* Redirect from /dashboard to / for Clerk compatibility */}
      <Route path="/dashboard" element={<Navigate to="/" replace />} />

      <Route path="/" element={
        <PerformanceRoute priority="high" skeletonVariant="dashboard">
          <DashboardHome role={role} />
        </PerformanceRoute>
      } />

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

      {/* Roblox Routes - Heavy 3D components with low priority */}
      <Route
        path="/roblox/*"
        element={
          <RoleGuard allow={["teacher", "admin"]}>
            <PerformanceRoute priority="low" skeletonVariant="dashboard">
              <TeacherRobloxDashboard />
            </PerformanceRoute>
          </RoleGuard>
        }
      />
      <Route
        path="/environment-preview/:environmentId"
        element={
          <RoleGuard allow={["teacher", "admin", "student"]}>
            <PerformanceRoute priority="low" skeletonVariant="dashboard">
              <EnvironmentPreviewPage />
            </PerformanceRoute>
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
      <Route
        path="/observability"
        element={
          <RoleGuard allow={["admin"]}>
            <PerformanceRoute priority="low" skeletonVariant="dashboard">
              <ObservabilityDashboard />
            </PerformanceRoute>
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

      {/* GPT-4.1 Migration Monitoring - Admin only */}
      <Route
        path="/gpt4-migration"
        element={
          <RoleGuard allowedRoles={["admin"]}>
            <GPT4MigrationDashboard />
          </RoleGuard>
        }
      />

      {/* Development Test Routes */}
      <Route path="/websocket-test" element={<WebSocketTest />} />
      <Route path="/websocket-demo" element={<WebSocketDemo />} />
      <Route path="/health" element={<HealthCheck />} />
      {/* Migration demo removed - not needed in production */}

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
