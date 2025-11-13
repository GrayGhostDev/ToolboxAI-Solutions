import axios, { AxiosError, AxiosResponse } from 'axios';
import { loadMockDataModule, type MockDataModule } from '../services/mock-loader';

// Check if we're in bypass/mock mode
const isBypassMode = () => {
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
  const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';
  return bypassAuth || useMockData;
};

type MockResolverEntry = {
  pattern: string;
  resolve: (mock: MockDataModule) => any;
};

const mockResponseEntries: MockResolverEntry[] = [
  { pattern: '/api/v1/schools/', resolve: (mock) => mock.mockSchools },
  { pattern: '/api/v1/users/', resolve: (mock) => mock.mockUsers },
  { pattern: '/api/v1/dashboard/overview', resolve: (mock) => mock.mockDashboardOverview },
  { pattern: '/api/v1/analytics/weekly_xp', resolve: (mock) => mock.mockAnalytics.weeklyXP },
  { pattern: '/api/v1/analytics/subject_mastery', resolve: (mock) => mock.mockAnalytics.subjectMastery },
  { pattern: '/api/v1/analytics/compliance/status', resolve: (mock) => mock.mockComplianceStatus },
  { pattern: '/api/v1/analytics/overview', resolve: (mock) => mock.mockAdminAnalytics.overview },
  { pattern: '/api/v1/analytics/user-activity', resolve: (mock) => mock.mockAdminAnalytics.userActivity },
  { pattern: '/api/v1/analytics/content-usage', resolve: (mock) => mock.mockAdminAnalytics.contentUsage },
  { pattern: '/api/v1/analytics/performance', resolve: (mock) => mock.mockAdminAnalytics.performance },
  { pattern: '/api/v1/gamification/leaderboard', resolve: (mock) => mock.mockGamification },
  { pattern: '/api/v1/messages/unread-count', resolve: (mock) => mock.mockUnreadMessages },
  { pattern: '/api/v1/messages', resolve: (mock) => mock.mockMessages },
  { pattern: '/messages', resolve: (mock) => mock.mockMessages },
  { pattern: '/classes', resolve: (mock) => mock.mockClasses },
  { pattern: '/lessons', resolve: (mock) => mock.mockLessons },
  { pattern: '/assessments', resolve: (mock) => mock.mockAssessments },
  { pattern: '/api/v1/reports', resolve: (mock) => mock.mockReports },
  { pattern: '/reports', resolve: (mock) => mock.mockReports },
  { pattern: '/api/v1/settings', resolve: (mock) => mock.mockSettings },
  { pattern: '/settings', resolve: (mock) => mock.mockSettings },
  { pattern: '/api/v1/students/data', resolve: (mock) => mock.mockStudentData },
  { pattern: '/api/v1/students/gameplay/missions', resolve: (mock) => mock.mockStudentGameplay.missions },
  { pattern: '/api/v1/students/gameplay/achievements', resolve: (mock) => mock.mockStudentGameplay.achievements },
  { pattern: '/api/v1/students/gameplay/leaderboard', resolve: (mock) => mock.mockStudentGameplay.leaderboard },
  { pattern: '/api/v1/students/gameplay/rewards', resolve: (mock) => mock.mockStudentGameplay.rewards },
  { pattern: '/api/v1/students/gameplay/worlds', resolve: (mock) => mock.mockStudentGameplay.gameWorlds },
  { pattern: '/api/v1/students/gameplay/challenges', resolve: (mock) => mock.mockStudentGameplay.challenges },
  { pattern: '/student/missions', resolve: (mock) => mock.mockStudentGameplay.missions },
  { pattern: '/student/achievements', resolve: (mock) => mock.mockStudentGameplay.achievements },
  { pattern: '/student/leaderboard', resolve: (mock) => mock.mockStudentGameplay.leaderboard },
  { pattern: '/student/rewards', resolve: (mock) => mock.mockStudentGameplay.rewards },
  { pattern: '/student/worlds', resolve: (mock) => mock.mockStudentGameplay.gameWorlds },
  { pattern: '/student/challenges', resolve: (mock) => mock.mockStudentGameplay.challenges },
  { pattern: '/api/v1/teachers/gradebook', resolve: (mock) => mock.mockTeacherGradebook },
  { pattern: '/api/v1/teachers/assessments', resolve: (mock) => mock.mockTeacherGradebook.assessments },
  { pattern: '/api/v1/teachers/class-performance', resolve: (mock) => mock.mockTeacherGradebook.classPerformance },
  { pattern: '/teacher/gradebook', resolve: (mock) => mock.mockTeacherGradebook },
  { pattern: '/teacher/assessments', resolve: (mock) => mock.mockTeacherGradebook.assessments },
  { pattern: '/teacher/performance', resolve: (mock) => mock.mockTeacherGradebook.classPerformance },
  { pattern: '/api/v1/admin/analytics', resolve: (mock) => mock.mockAdminAnalytics },
  { pattern: '/api/v1/admin/settings', resolve: (mock) => mock.mockSystemSettings },
  { pattern: '/api/v1/admin/activity-logs', resolve: (mock) => mock.mockActivityLogs },
  { pattern: '/api/v1/admin/users', resolve: (mock) => mock.mockUserManagement },
  { pattern: '/admin/analytics', resolve: (mock) => mock.mockAdminAnalytics },
  { pattern: '/admin/settings', resolve: (mock) => mock.mockSystemSettings },
  { pattern: '/admin/logs', resolve: (mock) => mock.mockActivityLogs },
  { pattern: '/admin/users', resolve: (mock) => mock.mockUserManagement },
  { pattern: '/api/v1/roblox/data', resolve: (mock) => mock.mockRobloxData },
  { pattern: '/api/v1/roblox/sessions', resolve: (mock) => mock.mockRobloxData.sessions },
  { pattern: '/api/v1/roblox/environments', resolve: (mock) => mock.mockRobloxData.environments },
  { pattern: '/api/v1/roblox/players', resolve: (mock) => mock.mockRobloxData.players },
  { pattern: '/roblox/data', resolve: (mock) => mock.mockRobloxData },
  { pattern: '/roblox/sessions', resolve: (mock) => mock.mockRobloxData.sessions },
  { pattern: '/roblox/environments', resolve: (mock) => mock.mockRobloxData.environments },
  { pattern: '/api/v1/integrations', resolve: (mock) => mock.mockIntegrations },
  { pattern: '/integrations', resolve: (mock) => mock.mockIntegrations },
];

const stripQuery = (value: string) => value.replace(/\?.*$/, '');

const findMockEntry = (url: string) =>
  mockResponseEntries.find(({ pattern }) => url.includes(stripQuery(pattern)));

const resolveMockResponse = async (url: string) => {
  const match = findMockEntry(url);
  if (!match) return null;

  const mockModule = await loadMockDataModule();
  return {
    mockModule,
    data: match.resolve(mockModule),
  };
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
      const mockResult = await resolveMockResponse(url);

      if (mockResult) {
        config.adapter = async () => {
          await mockResult.mockModule.mockDelay();
          return {
            data: mockResult.data,
            status: 200,
            statusText: 'OK',
            headers: {},
            config,
          } as AxiosResponse;
        };
      }
    }

    // Add auth token if available
    // Try multiple token keys for compatibility
    const token = localStorage.getItem('toolboxai_auth_token') ||
                  localStorage.getItem('auth_token') ||
                  localStorage.getItem('access_token');
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
      const mockResult = await resolveMockResponse(url);

      if (mockResult) {
        await mockResult.mockModule.mockDelay();
        return { data: mockResult.data, status: 200 } as AxiosResponse;
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
