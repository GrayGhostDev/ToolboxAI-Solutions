export type UserRole = 'admin' | 'teacher' | 'student' | 'parent';

export interface RolePermissions {
  viewDashboard: boolean;
  viewAnalytics: boolean;
  manageUsers: boolean;
  manageClasses: boolean;
  manageLessons: boolean;
  viewAssessments: boolean;
  createAssessments: boolean;
  viewLeaderboard: boolean;
  viewCompliance: boolean;
  manageIntegrations: boolean;
  viewReports: boolean;
  sendMessages: boolean;
  enterRobloxWorld: boolean;
  customizeAvatar: boolean;
}

export const ROLE_PERMISSIONS: Record<UserRole, RolePermissions> = {
  admin: {
    viewDashboard: true,
    viewAnalytics: true,
    manageUsers: true,
    manageClasses: true,
    manageLessons: true,
    viewAssessments: true,
    createAssessments: true,
    viewLeaderboard: true,
    viewCompliance: true,
    manageIntegrations: true,
    viewReports: true,
    sendMessages: true,
    enterRobloxWorld: false,
    customizeAvatar: false,
  },
  teacher: {
    viewDashboard: true,
    viewAnalytics: true,
    manageUsers: false,
    manageClasses: true,
    manageLessons: true,
    viewAssessments: true,
    createAssessments: true,
    viewLeaderboard: true,
    viewCompliance: false,
    manageIntegrations: false,
    viewReports: true,
    sendMessages: true,
    enterRobloxWorld: true,
    customizeAvatar: false,
  },
  student: {
    viewDashboard: true,
    viewAnalytics: false,
    manageUsers: false,
    manageClasses: false,
    manageLessons: false,
    viewAssessments: true,
    createAssessments: false,
    viewLeaderboard: true,
    viewCompliance: false,
    manageIntegrations: false,
    viewReports: true,
    sendMessages: false,
    enterRobloxWorld: true,
    customizeAvatar: true,
  },
  parent: {
    viewDashboard: true,
    viewAnalytics: false,
    manageUsers: false,
    manageClasses: false,
    manageLessons: false,
    viewAssessments: true,
    createAssessments: false,
    viewLeaderboard: false,
    viewCompliance: false,
    manageIntegrations: false,
    viewReports: true,
    sendMessages: true,
    enterRobloxWorld: false,
    customizeAvatar: false,
  },
};