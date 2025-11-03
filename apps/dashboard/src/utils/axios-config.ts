import axios, { AxiosError, AxiosResponse } from 'axios';
import {
  mockDelay,
  mockSchools,
  mockUsers,
  mockDashboardOverview,
  mockAnalytics,
  mockGamification,
  mockComplianceStatus,
  mockUnreadMessages,
  mockClasses,
  mockLessons,
  mockAssessments,
  mockMessages,
  mockReports,
  mockSettings,
  mockStudentData,
  mockAdminAnalytics,
  mockSystemSettings,
  mockActivityLogs,
  mockUserManagement,
  mockRobloxData,
  mockStudentGameplay,
  mockTeacherGradebook,
  mockIntegrations
} from '../services/mock-data';

// Check if we're in bypass/mock mode
const isBypassMode = () => {
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
  const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';
  return bypassAuth || useMockData;
};

// Mock response data for various endpoints
const mockResponses: Record<string, any> = {
  // Core endpoints
  '/api/v1/schools/': mockSchools,
  '/api/v1/users/': mockUsers,
  '/api/v1/dashboard/overview': mockDashboardOverview,

  // Analytics endpoints
  '/api/v1/analytics/weekly_xp': mockAnalytics.weeklyXP,
  '/api/v1/analytics/subject_mastery': mockAnalytics.subjectMastery,
  '/api/v1/analytics/compliance/status': mockComplianceStatus,
  '/api/v1/analytics/overview': mockAdminAnalytics.overview,
  '/api/v1/analytics/user-activity': mockAdminAnalytics.userActivity,
  '/api/v1/analytics/content-usage': mockAdminAnalytics.contentUsage,
  '/api/v1/analytics/performance': mockAdminAnalytics.performance,

  // Gamification endpoints
  '/api/v1/gamification/leaderboard': mockGamification,

  // Messages & Communications
  '/api/v1/messages/unread-count': mockUnreadMessages,
  '/api/v1/messages': mockMessages,
  '/messages': mockMessages,

  // Educational content
  '/classes': mockClasses,
  '/lessons': mockLessons,
  '/assessments': mockAssessments,

  // Reports
  '/api/v1/reports': mockReports,
  '/reports': mockReports,

  // Settings
  '/api/v1/settings': mockSettings,
  '/settings': mockSettings,

  // Student endpoints
  '/api/v1/students/data': mockStudentData,
  '/api/v1/students/gameplay/missions': mockStudentGameplay.missions,
  '/api/v1/students/gameplay/achievements': mockStudentGameplay.achievements,
  '/api/v1/students/gameplay/leaderboard': mockStudentGameplay.leaderboard,
  '/api/v1/students/gameplay/rewards': mockStudentGameplay.rewards,
  '/api/v1/students/gameplay/worlds': mockStudentGameplay.gameWorlds,
  '/api/v1/students/gameplay/challenges': mockStudentGameplay.challenges,
  '/student/missions': mockStudentGameplay.missions,
  '/student/achievements': mockStudentGameplay.achievements,
  '/student/leaderboard': mockStudentGameplay.leaderboard,
  '/student/rewards': mockStudentGameplay.rewards,
  '/student/worlds': mockStudentGameplay.gameWorlds,
  '/student/challenges': mockStudentGameplay.challenges,

  // Teacher endpoints
  '/api/v1/teachers/gradebook': mockTeacherGradebook,
  '/api/v1/teachers/assessments': mockTeacherGradebook.assessments,
  '/api/v1/teachers/class-performance': mockTeacherGradebook.classPerformance,
  '/teacher/gradebook': mockTeacherGradebook,
  '/teacher/assessments': mockTeacherGradebook.assessments,
  '/teacher/performance': mockTeacherGradebook.classPerformance,

  // Admin endpoints
  '/api/v1/admin/analytics': mockAdminAnalytics,
  '/api/v1/admin/settings': mockSystemSettings,
  '/api/v1/admin/activity-logs': mockActivityLogs,
  '/api/v1/admin/users': mockUserManagement,
  '/admin/analytics': mockAdminAnalytics,
  '/admin/settings': mockSystemSettings,
  '/admin/logs': mockActivityLogs,
  '/admin/users': mockUserManagement,

  // Roblox endpoints
  '/api/v1/roblox/data': mockRobloxData,
  '/api/v1/roblox/sessions': mockRobloxData.sessions,
  '/api/v1/roblox/environments': mockRobloxData.environments,
  '/api/v1/roblox/players': mockRobloxData.players,
  '/roblox/data': mockRobloxData,
  '/roblox/sessions': mockRobloxData.sessions,
  '/roblox/environments': mockRobloxData.environments,

  // Integrations
  '/api/v1/integrations': mockIntegrations,
  '/integrations': mockIntegrations,
};

// Configure axios defaults
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8009';
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Request interceptor - check for bypass mode
axios.interceptors.request.use(
  async (config) => {
    // In bypass mode, intercept and return mock data
    if (isBypassMode()) {
      const url = config.url || '';

      // Find matching mock response
      for (const [pattern, response] of Object.entries(mockResponses)) {
        if (url.includes(pattern.replace(/\?.*$/, ''))) {
          // Cancel the real request and return mock data
          config.adapter = async () => {
            await mockDelay(); // Simulate network delay
            return {
              data: response,
              status: 200,
              statusText: 'OK',
              headers: {},
              config,
            } as AxiosResponse;
          };
          break;
        }
      }
    }

    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors gracefully
axios.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // In bypass mode, return mock data even for failed requests
    if (isBypassMode() && error.config) {
      const url = error.config.url || '';

      // Find matching mock response
      for (const [pattern, response] of Object.entries(mockResponses)) {
        if (url.includes(pattern.replace(/\?.*$/, ''))) {
          await mockDelay();
          return { data: response, status: 200 } as AxiosResponse;
        }
      }

      // Return generic success for unmatched endpoints in bypass mode
      console.log(`[Mock Mode] No mock data for: ${url}, returning empty response`);
      return { data: {}, status: 200 } as AxiosResponse;
    }

    // Handle specific error cases
    if (error.code === 'ECONNREFUSED') {
      console.warn('[API] Backend server is not running. Using fallback data.');

      // Return empty response for connection refused in bypass mode
      if (isBypassMode()) {
        return { data: {}, status: 200 } as AxiosResponse;
      }
    }

    // Log error for debugging (but not ECONNREFUSED spam)
    if (error.code !== 'ECONNREFUSED') {
      console.error('[API Error]', error.message);
    }

    return Promise.reject(error);
  }
);

// Export configured axios instance
export default axios;

// Utility function to check if mock mode is active
export { isBypassMode };