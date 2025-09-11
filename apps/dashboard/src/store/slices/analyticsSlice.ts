import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import * as api from '../../services/api';

interface PlatformMetrics {
  totalUsers: number;
  totalSchools: number;
  totalLessons: number;
  totalAssessments: number;
  activeUsers: number;
  averageCompletion: number;
  averageEngagement: number;
  growthRate: number;
}

interface UserAnalytics {
  newUsersToday: number;
  newUsersThisWeek: number;
  newUsersThisMonth: number;
  usersByRole: {
    students: number;
    teachers: number;
    parents: number;
    admins: number;
  };
  userActivity: Array<{
    date: string;
    activeUsers: number;
    newUsers: number;
  }>;
}

interface PerformanceMetrics {
  topPerformers: Array<{
    id: string;
    name: string;
    xp: number;
    badges: number;
    level: number;
    completionRate: number;
  }>;
  strugglingStudents: Array<{
    id: string;
    name: string;
    xp: number;
    completionRate: number;
    lastActive: string;
  }>;
  averageXPPerStudent: number;
  averageCompletionTime: number;
}

interface SubjectAnalytics {
  subjects: Array<{
    name: string;
    averageScore: number;
    completionRate: number;
    totalLessons: number;
    totalStudents: number;
    trend: 'up' | 'down' | 'stable';
  }>;
  mostPopularSubject: string;
  leastPopularSubject: string;
}

interface EngagementMetrics {
  robloxSessions: number;
  averageSessionDuration: number;
  popularWorlds: Array<{
    id: string;
    name: string;
    sessions: number;
    uniqueUsers: number;
  }>;
  peakUsageHours: Array<{
    hour: number;
    users: number;
  }>;
  deviceBreakdown: {
    desktop: number;
    mobile: number;
    tablet: number;
  };
}

interface ComplianceMetrics {
  coppaCompliant: boolean;
  ferpaCompliant: boolean;
  gdprCompliant: boolean;
  pendingConsents: number;
  dataRetentionDays: number;
  lastAuditDate: string;
  issues: string[];
}

interface AnalyticsState {
  platform: PlatformMetrics | null;
  users: UserAnalytics | null;
  performance: PerformanceMetrics | null;
  subjects: SubjectAnalytics | null;
  engagement: EngagementMetrics | null;
  compliance: ComplianceMetrics | null;
  weeklyXP: Array<{ date: string; xp: number }>;
  subjectMastery: Array<{ subject: string; mastery: number }>;
  loading: boolean;
  error: string | null;
  timeRange: string;
  lastUpdated: string | null;
}

const initialState: AnalyticsState = {
  platform: null,
  users: null,
  performance: null,
  subjects: null,
  engagement: null,
  compliance: null,
  weeklyXP: [],
  subjectMastery: [],
  loading: false,
  error: null,
  timeRange: '30d',
  lastUpdated: null,
};

// Async thunks
export const fetchPlatformAnalytics = createAsyncThunk(
  'analytics/fetchPlatform',
  async (timeRange?: 'all' | 'weekly' | 'daily' | 'monthly') => {
    const validTimeRange = timeRange || 'monthly';
    // Fetch from multiple endpoints and aggregate
    const [dashboardData, weeklyXP, subjectMastery] = await Promise.all([
      api.getDashboardOverview('admin'),
      api.getWeeklyXP(),
      api.getSubjectMastery(),
    ]);
    
    return {
      dashboard: dashboardData,
      weeklyXP,
      subjectMastery,
      timestamp: new Date().toISOString(),
    };
  }
);

export const fetchUserAnalytics = createAsyncThunk(
  'analytics/fetchUsers',
  async (timeRange: string = '30d') => {
    // This would call specific user analytics endpoints
    // For now, we'll use the dashboard overview
    const response = await api.getDashboardOverview('admin');
    return response;
  }
);

export const fetchPerformanceMetrics = createAsyncThunk(
  'analytics/fetchPerformance',
  async (filters?: { classId?: string; timeRange?: string }) => {
    const timeframe = (filters?.timeRange === 'all' || filters?.timeRange === 'weekly' || 
                     filters?.timeRange === 'daily' || filters?.timeRange === 'monthly') 
                     ? filters.timeRange : 'all';
    const leaderboard = await api.getLeaderboard(filters?.classId, timeframe);
    return leaderboard;
  }
);

export const fetchSubjectAnalytics = createAsyncThunk(
  'analytics/fetchSubjects',
  async () => {
    const mastery = await api.getSubjectMastery();
    return mastery;
  }
);

export const fetchEngagementMetrics = createAsyncThunk(
  'analytics/fetchEngagement',
  async (timeRange: string = '30d') => {
    // This would call Roblox integration endpoints
    // Placeholder for now
    return {
      sessions: 0,
      duration: 0,
      worlds: [],
    };
  }
);

export const fetchComplianceMetrics = createAsyncThunk(
  'analytics/fetchCompliance',
  async () => {
    const status = await api.getComplianceStatus();
    return status;
  }
);

export const refreshAllAnalytics = createAsyncThunk(
  'analytics/refreshAll',
  async (timeRange: string = '30d', { dispatch }) => {
    // Map string timeRange to valid platform analytics timeRange
    const validTimeRange: 'all' | 'weekly' | 'daily' | 'monthly' = 
      timeRange === 'all' || timeRange === 'weekly' || timeRange === 'daily' || timeRange === 'monthly' 
        ? timeRange 
        : 'monthly';
    
    // Dispatch all fetch actions
    const promises = [
      dispatch(fetchPlatformAnalytics(validTimeRange)),
      dispatch(fetchUserAnalytics(timeRange)),
      dispatch(fetchPerformanceMetrics({ timeRange })),
      dispatch(fetchSubjectAnalytics()),
      dispatch(fetchEngagementMetrics(timeRange)),
      dispatch(fetchComplianceMetrics()),
    ];
    
    await Promise.all(promises);
    return { timestamp: new Date().toISOString() };
  }
);

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    setTimeRange: (state, action: PayloadAction<string>) => {
      state.timeRange = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateMetric: (state, action: PayloadAction<{ metric: string; value: any }>) => {
      // Update specific metric in real-time
      const { metric, value } = action.payload;
      if (state.platform && metric in state.platform) {
        (state.platform as any)[metric] = value;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch platform analytics
    builder
      .addCase(fetchPlatformAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPlatformAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        // Transform ProgressPoint[] to expected format
        state.weeklyXP = (action.payload.weeklyXP || []).map((point: any) => ({
          date: point.x || point.date || '',
          xp: point.y || point.xp || 0
        }));
        state.subjectMastery = action.payload.subjectMastery || [];
        state.lastUpdated = action.payload.timestamp;
        
        // Parse dashboard data into platform metrics
        if (action.payload.dashboard) {
          const metrics = action.payload.dashboard.metrics || {};
          state.platform = {
            totalUsers: metrics.totalStudents || metrics.totalTeachers || 0,
            totalSchools: 1, // Default value since not in DashboardMetrics
            totalLessons: 0, // Default value since not in DashboardMetrics
            totalAssessments: 0, // Default value since not in DashboardMetrics
            activeUsers: metrics.activeClasses || 0,
            averageCompletion: metrics.averageProgress || 0,
            averageEngagement: 0,
            growthRate: 0,
          };
        }
      })
      .addCase(fetchPlatformAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch platform analytics';
      });

    // Fetch performance metrics
    builder
      .addCase(fetchPerformanceMetrics.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchPerformanceMetrics.fulfilled, (state, action) => {
        state.loading = false;
        
        if (Array.isArray(action.payload)) {
          const topPerformers = action.payload.slice(0, 10).map(entry => ({
            id: entry.studentId,
            name: entry.displayName,
            xp: entry.xp,
            badges: entry.badgeCount,
            level: entry.level,
            completionRate: 0,
          }));
          
          state.performance = {
            topPerformers,
            strugglingStudents: [],
            averageXPPerStudent: topPerformers.reduce((acc, p) => acc + p.xp, 0) / topPerformers.length,
            averageCompletionTime: 0,
          };
        }
      })
      .addCase(fetchPerformanceMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch performance metrics';
      });

    // Fetch subject analytics
    builder
      .addCase(fetchSubjectAnalytics.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchSubjectAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        
        if (Array.isArray(action.payload)) {
          const subjects = action.payload.map(item => ({
            name: item.subject,
            averageScore: item.mastery || 0, // Use mastery as averageScore
            completionRate: item.mastery || 0, // Use mastery as completionRate
            totalLessons: 0,
            totalStudents: 0,
            trend: 'stable' as const,
          }));
          
          state.subjects = {
            subjects,
            mostPopularSubject: subjects[0]?.name || '',
            leastPopularSubject: subjects[subjects.length - 1]?.name || '',
          };
        }
      })
      .addCase(fetchSubjectAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch subject analytics';
      });

    // Fetch compliance metrics
    builder
      .addCase(fetchComplianceMetrics.fulfilled, (state, action) => {
        state.compliance = {
          coppaCompliant: action.payload.coppa?.status === 'compliant',
          ferpaCompliant: action.payload.ferpa?.status === 'compliant',
          gdprCompliant: action.payload.gdpr?.status === 'compliant',
          pendingConsents: 0,
          dataRetentionDays: 365,
          lastAuditDate: action.payload.lastAudit,
          issues: [
            ...(action.payload.coppa?.issues || []),
            ...(action.payload.ferpa?.issues || []),
            ...(action.payload.gdpr?.issues || []),
          ],
        };
      });

    // Refresh all analytics
    builder
      .addCase(refreshAllAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(refreshAllAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        state.lastUpdated = action.payload.timestamp;
      })
      .addCase(refreshAllAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to refresh analytics';
      });
  },
});

export const { setTimeRange, clearError, updateMetric } = analyticsSlice.actions;
export default analyticsSlice.reducer;