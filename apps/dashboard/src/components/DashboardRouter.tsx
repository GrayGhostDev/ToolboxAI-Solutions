import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../utils/mui-imports';
/**
 * Dashboard Router Component
 * Routes users to appropriate dashboard based on their role
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserRole } from '../types/roles';

// Import role-specific dashboards (these will be created)
import AdminDashboard from './dashboards/AdminDashboard';
import TeacherDashboard from './dashboards/TeacherDashboard';
import StudentDashboard from './dashboards/StudentDashboard';
import ParentDashboard from './dashboards/ParentDashboard';

// Import shared components
import ProfilePage from './shared/ProfilePage';
import SettingsPage from './shared/SettingsPage';
import NotFoundPage from './shared/NotFoundPage';
import LoadingSpinner from './shared/LoadingSpinner';

// Protected route wrapper
const ProtectedRoute: React.FunctionComponent<{
  children: React.ReactNode;
  requiredRole?: UserRole;
  permission?: string;
}> = ({ children, requiredRole, permission }) => {
  const { user, isAuthenticated, checkPermission } = useAuth();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  if (permission && !checkPermission(permission)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};

const DashboardRouter: React.FunctionComponent<Record<string, any>> = () => {
  const { user, userConfig, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading dashboard..." />;
  }

  if (!user || !userConfig) {
    return <Navigate to="/login" replace />;
  }

  // Route based on user role
  const getDashboardComponent = () => {
    switch (user.role) {
      case 'admin':
        return <AdminDashboard />;
      case 'teacher':
        return <TeacherDashboard />;
      case 'student':
        return <StudentDashboard />;
      case 'parent':
        return <ParentDashboard />;
      default:
        return <Navigate to="/login" replace />;
    }
  };

  return (
    <Routes>
      {/* Default route - render role-specific dashboard component */}
      <Route path="/" element={getDashboardComponent()} />

      {/* Admin Routes */}
      <Route path="/admin/*" element={
        <ProtectedRoute requiredRole="admin">
          <Routes>
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="users/*" element={<AdminDashboard section="users" />} />
            <Route path="schools/*" element={<AdminDashboard section="schools" />} />
            <Route path="content/*" element={<AdminDashboard section="content" />} />
            <Route path="analytics" element={<AdminDashboard section="analytics" />} />
            <Route path="integrations" element={<AdminDashboard section="integrations" />} />
            <Route path="compliance" element={<AdminDashboard section="compliance" />} />
            <Route path="support" element={<AdminDashboard section="support" />} />
            <Route path="settings" element={<SettingsPage />} />
          </Routes>
        </ProtectedRoute>
      } />

      {/* Teacher Routes */}
      <Route path="/teacher/*" element={
        <ProtectedRoute requiredRole="teacher">
          <Routes>
            <Route path="dashboard" element={<TeacherDashboard />} />
            <Route path="classes/*" element={<TeacherDashboard section="classes" />} />
            <Route path="lessons/*" element={<TeacherDashboard section="lessons" />} />
            <Route path="assessments/*" element={<TeacherDashboard section="assessments" />} />
            <Route path="students/*" element={<TeacherDashboard section="students" />} />
            <Route path="roblox" element={<TeacherDashboard section="roblox" />} />
            <Route path="messages" element={<TeacherDashboard section="messages" />} />
            <Route path="resources" element={<TeacherDashboard section="resources" />} />
            <Route path="settings" element={<SettingsPage />} />
          </Routes>
        </ProtectedRoute>
      } />

      {/* Student Routes */}
      <Route path="/student/*" element={
        <ProtectedRoute requiredRole="student">
          <Routes>
            <Route path="dashboard" element={<StudentDashboard />} />
            <Route path="classes" element={<StudentDashboard section="classes" />} />
            <Route path="lessons" element={<StudentDashboard section="lessons" />} />
            <Route path="assignments" element={<StudentDashboard section="assignments" />} />
            <Route path="roblox" element={<StudentDashboard section="roblox" />} />
            <Route path="progress" element={<StudentDashboard section="progress" />} />
            <Route path="achievements" element={<StudentDashboard section="achievements" />} />
            <Route path="leaderboard" element={<StudentDashboard section="leaderboard" />} />
            <Route path="profile" element={<ProfilePage />} />
          </Routes>
        </ProtectedRoute>
      } />

      {/* Parent Routes */}
      <Route path="/parent/*" element={
        <ProtectedRoute requiredRole="parent">
          <Routes>
            <Route path="dashboard" element={<ParentDashboard />} />
            <Route path="children" element={<ParentDashboard section="children" />} />
            <Route path="progress" element={<ParentDashboard section="progress" />} />
            <Route path="attendance" element={<ParentDashboard section="attendance" />} />
            <Route path="assignments" element={<ParentDashboard section="assignments" />} />
            <Route path="messages" element={<ParentDashboard section="messages" />} />
            <Route path="teachers" element={<ParentDashboard section="teachers" />} />
            <Route path="calendar" element={<ParentDashboard section="calendar" />} />
            <Route path="settings" element={<SettingsPage />} />
          </Routes>
        </ProtectedRoute>
      } />

      {/* Shared routes */}
      <Route path="/profile" element={
        <ProtectedRoute>
          <ProfilePage />
        </ProtectedRoute>
      } />

      <Route path="/settings" element={
        <ProtectedRoute>
          <SettingsPage />
        </ProtectedRoute>
      } />

      {/* Error pages */}
      <Route path="/unauthorized" element={
        <Box style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh'
        }}>
          <Typography variant="h4" gutterBottom>Unauthorized Access</Typography>
          <Typography variant="body1" gutterBottom>You don't have permission to access this page.</Typography>
          <Button variant="contained" onClick={() => window.history.back()}>Go Back</Button>
        </Box>
      } />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default DashboardRouter;
