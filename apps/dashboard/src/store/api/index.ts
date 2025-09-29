import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query';
import { RootState } from '../index';
import { addNotification } from '../slices/uiSlice';
import {
  API_BASE_URL,
  AUTH_TOKEN_KEY,
  AUTH_REFRESH_TOKEN_KEY
} from '../../config';
import type {
  DashboardOverview,
  ClassSummary,
  ClassDetails,
  Lesson,
  Assessment,
  AssessmentSubmission,
  Message,
  User,
  UserCreate,
  UserUpdate,
  AuthResponse,
  StudentProgress,
  Badge,
  LeaderboardEntry,
  XPTransaction,
  ComplianceStatus,
  RobloxWorld,
  ProgressPoint,
  ApiResponse,
} from '../../types';

// Enhanced base query with automatic token refresh
const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const baseQuery = fetchBaseQuery({
    baseUrl: API_BASE_URL,
    timeout: 15000,
    prepareHeaders: (headers, { getState }) => {
      headers.set('Content-Type', 'application/json');

      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }

      return headers;
    },
  });

  let result = await baseQuery(args, api, extraOptions);

  // Handle 401 Unauthorized - Token refresh
  if (result.error && result.error.status === 401) {
    const refreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);

    if (refreshToken) {
      try {
        // Attempt to refresh token
        const refreshResult = await baseQuery(
          {
            url: '/api/v1/auth/refresh',
            method: 'POST',
            body: { refresh_token: refreshToken },
          },
          api,
          extraOptions
        );

        if (refreshResult.data) {
          const { accessToken, refreshToken: newRefreshToken } = refreshResult.data as AuthResponse;

          // Update tokens
          localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
          localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, newRefreshToken);

          // Retry original request
          result = await baseQuery(args, api, extraOptions);
        } else {
          // Refresh failed, clear tokens and redirect
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);

          api.dispatch(addNotification({
            type: 'error',
            message: 'Session expired. Please log in again.',
            autoHide: false,
          }));

          setTimeout(() => {
            window.location.href = '/login';
          }, 2000);
        }
      } catch (error) {
        // Refresh failed
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);

        api.dispatch(addNotification({
          type: 'error',
          message: 'Session expired. Please log in again.',
          autoHide: false,
        }));

        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      }
    }
  }

  // Handle success notifications for mutations
  if (result.data && typeof args === 'object' && 'method' in args) {
    const method = args.method?.toLowerCase();
    const url = typeof args === 'string' ? args : args.url;

    if (method && ['post', 'put', 'delete'].includes(method)) {
      let message = '';

      if (url.includes('/register')) {
        message = 'Registration successful! Welcome to ToolBoxAI.';
      } else if (url.includes('/login')) {
        message = 'Welcome back! Successfully logged in.';
      } else if (url.includes('/classes') && method === 'post') {
        message = 'Class created successfully!';
      } else if (url.includes('/classes') && method === 'put') {
        message = 'Class updated successfully!';
      } else if (url.includes('/classes') && method === 'delete') {
        message = 'Class deleted successfully!';
      } else if (url.includes('/lessons') && method === 'post') {
        message = 'Lesson created successfully!';
      } else if (url.includes('/lessons') && method === 'put') {
        message = 'Lesson updated successfully!';
      } else if (url.includes('/assessments') && method === 'post') {
        message = 'Assessment created successfully!';
      } else if (url.includes('/messages') && method === 'post') {
        message = 'Message sent successfully!';
      }

      if (message) {
        api.dispatch(addNotification({
          type: 'success',
          message,
          autoHide: true,
        }));
      }
    }
  }

  // Handle error notifications
  if (result.error) {
    let errorMessage = 'An unexpected error occurred. Please try again.';

    if (result.error.status === 'FETCH_ERROR') {
      errorMessage = 'Unable to connect to the server. Please check your internet connection.';
    } else if (result.error.status === 'TIMEOUT_ERROR') {
      errorMessage = 'Request timed out. Please try again.';
    } else if (result.error.data) {
      const errorData = result.error.data as any;

      if (errorData.message) {
        errorMessage = errorData.message;
      } else if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          const errors = errorData.detail.map((err: any) =>
            err.msg || err.message || 'Validation error'
          );
          errorMessage = errors.join(', ');
        } else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        }
      } else {
        // Provide status-specific messages
        switch (result.error.status) {
          case 400:
            errorMessage = 'Invalid request. Please check your input.';
            break;
          case 403:
            errorMessage = 'You do not have permission to perform this action.';
            break;
          case 404:
            errorMessage = 'The requested resource was not found.';
            break;
          case 409:
            errorMessage = 'This action conflicts with existing data.';
            break;
          case 422:
            errorMessage = 'Validation error. Please check your input.';
            break;
          case 429:
            errorMessage = 'Too many requests. Please slow down.';
            break;
          case 500:
            errorMessage = 'Server error. Our team has been notified.';
            break;
          case 502:
          case 503:
            errorMessage = 'Service temporarily unavailable. Please try again later.';
            break;
        }
      }
    }

    // Only show error notifications for non-authentication errors
    if (result.error.status !== 401) {
      api.dispatch(addNotification({
        type: 'error',
        message: errorMessage,
        autoHide: false,
      }));
    }
  }

  return result;
};

// Main API slice
export const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'Dashboard',
    'Class',
    'Lesson',
    'Assessment',
    'Message',
    'User',
    'Progress',
    'Badge',
    'Leaderboard',
    'Compliance',
    'RobloxWorld',
    'Analytics',
  ],
  keepUnusedDataFor: 300, // 5 minutes cache
  refetchOnMountOrArgChange: 300, // Refetch if data is older than 5 minutes
  refetchOnFocus: true,
  refetchOnReconnect: true,
  endpoints: (builder) => ({
    // Dashboard endpoints
    getDashboardOverview: builder.query<DashboardOverview, string | void>({
      query: (role) => '/api/v1/dashboard/overview',
      providesTags: ['Dashboard'],
      keepCachedData: true,
      transformResponse: (response: any) => {
        // Handle both direct data and wrapped ApiResponse format
        return response.data || response;
      },
    }),

    // Authentication endpoints
    login: builder.mutation<AuthResponse, { username: string; password: string }>({
      query: (credentials) => ({
        url: '/api/v1/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['Dashboard', 'User'],
    }),

    register: builder.mutation<AuthResponse, {
      email: string;
      password: string;
      displayName: string;
      role: string;
    }>({
      query: (data) => {
        const [firstName, ...lastNameParts] = data.displayName.split(' ');
        const lastName = lastNameParts.join(' ') || firstName;

        return {
          url: '/api/v1/auth/register',
          method: 'POST',
          body: {
            email: data.email,
            password: data.password,
            username: data.email.split('@')[0],
            first_name: firstName,
            last_name: lastName,
            role: data.role,
          },
        };
      },
      transformResponse: (response: any) => ({
        accessToken: response.access_token || response.accessToken,
        refreshToken: response.refresh_token || response.refreshToken,
        expiresIn: response.expires_in || 3600,
        user: {
          id: response.user.id,
          email: response.user.email,
          username: response.user.username,
          firstName: response.user.first_name || response.user.firstName,
          lastName: response.user.last_name || response.user.lastName,
          displayName: response.user.display_name || response.user.displayName ||
                      `${response.user.first_name} ${response.user.last_name}`,
          avatarUrl: response.user.avatar_url || response.user.avatarUrl,
          role: response.user.role,
          schoolId: response.user.school_id || response.user.schoolId,
          schoolName: response.user.school_name,
          classIds: response.user.class_ids || response.user.classIds || [],
          parentIds: response.user.parent_ids || [],
          childIds: response.user.child_ids || [],
          isActive: response.user.is_active ?? true,
          isVerified: response.user.is_verified ?? false,
          totalXP: response.user.total_xp || 0,
          level: response.user.level || 1,
          lastLogin: response.user.last_login,
          createdAt: response.user.created_at || new Date().toISOString(),
          updatedAt: response.user.updated_at || new Date().toISOString(),
          status: response.user.status || 'active',
        },
      }),
      invalidatesTags: ['Dashboard', 'User'],
    }),

    refreshToken: builder.mutation<AuthResponse, { refresh_token: string }>({
      query: (data) => ({
        url: '/api/v1/auth/refresh',
        method: 'POST',
        body: data,
      }),
    }),

    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/api/v1/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['Dashboard', 'User', 'Class', 'Lesson', 'Assessment', 'Message'],
    }),

    // Classes endpoints
    getClasses: builder.query<ClassSummary[], void>({
      query: () => '/api/v1/classes/',
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Class' as const, id })),
              { type: 'Class', id: 'LIST' },
            ]
          : [{ type: 'Class', id: 'LIST' }],
      keepCachedData: true,
    }),

    getClass: builder.query<ClassDetails, string>({
      query: (id) => `/api/v1/classes/${id}`,
      providesTags: (result, error, id) => [{ type: 'Class', id }],
    }),

    createClass: builder.mutation<ClassSummary, Partial<ClassSummary>>({
      query: (data) => ({
        url: '/api/v1/classes/',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [{ type: 'Class', id: 'LIST' }, 'Dashboard'],
      // Optimistic update
      async onQueryStarted(newClass, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          api.util.updateQueryData('getClasses', undefined, (draft) => {
            const optimisticClass = {
              id: `temp-${Date.now()}`,
              name: newClass.name || 'New Class',
              subject: newClass.subject || '',
              grade_level: newClass.grade_level || 1,
              teacher_id: newClass.teacher_id || '',
              teacher_name: newClass.teacher_name || '',
              student_count: 0,
              max_students: newClass.max_students || 30,
              is_active: true,
              is_online: false,
              average_progress: 0,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              ...newClass,
            } as ClassSummary;

            draft.push(optimisticClass);
          })
        );

        try {
          const { data: actualClass } = await queryFulfilled;
          // Replace optimistic update with actual data
          dispatch(
            api.util.updateQueryData('getClasses', undefined, (draft) => {
              const index = draft.findIndex(c => c.id.startsWith('temp-'));
              if (index !== -1) {
                draft[index] = actualClass;
              }
            })
          );
        } catch {
          // Rollback optimistic update on error
          patchResult.undo();
        }
      },
    }),

    updateClass: builder.mutation<ClassSummary, { id: string; data: Partial<ClassSummary> }>({
      query: ({ id, data }) => ({
        url: `/api/v1/classes/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Class', id },
        { type: 'Class', id: 'LIST' },
      ],
      // Optimistic update
      async onQueryStarted({ id, data }, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          api.util.updateQueryData('getClasses', undefined, (draft) => {
            const classToUpdate = draft.find(c => c.id === id);
            if (classToUpdate) {
              Object.assign(classToUpdate, data, { updated_at: new Date().toISOString() });
            }
          })
        );

        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      },
    }),

    deleteClass: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/v1/classes/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Class', id },
        { type: 'Class', id: 'LIST' },
        'Dashboard',
      ],
      // Optimistic update
      async onQueryStarted(id, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          api.util.updateQueryData('getClasses', undefined, (draft) => {
            const index = draft.findIndex(c => c.id === id);
            if (index !== -1) {
              draft.splice(index, 1);
            }
          })
        );

        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      },
    }),

    // Lessons endpoints
    getLessons: builder.query<Lesson[], string | void>({
      query: (classId) => ({
        url: '/api/v1/lessons',
        params: classId ? { classId } : undefined,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Lesson' as const, id })),
              { type: 'Lesson', id: 'LIST' },
            ]
          : [{ type: 'Lesson', id: 'LIST' }],
    }),

    getLesson: builder.query<Lesson, string>({
      query: (id) => `/api/v1/lessons/${id}`,
      providesTags: (result, error, id) => [{ type: 'Lesson', id }],
    }),

    createLesson: builder.mutation<Lesson, Partial<Lesson>>({
      query: (data) => ({
        url: '/api/v1/lessons',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [{ type: 'Lesson', id: 'LIST' }],
    }),

    updateLesson: builder.mutation<Lesson, { id: string; data: Partial<Lesson> }>({
      query: ({ id, data }) => ({
        url: `/api/v1/lessons/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Lesson', id },
        { type: 'Lesson', id: 'LIST' },
      ],
    }),

    deleteLesson: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/v1/lessons/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Lesson', id },
        { type: 'Lesson', id: 'LIST' },
      ],
    }),

    // Assessments endpoints
    getAssessments: builder.query<Assessment[], string | void>({
      query: (classId) => ({
        url: '/api/v1/assessments/',
        params: classId ? { class_id: classId } : undefined,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Assessment' as const, id })),
              { type: 'Assessment', id: 'LIST' },
            ]
          : [{ type: 'Assessment', id: 'LIST' }],
    }),

    getAssessment: builder.query<Assessment, string>({
      query: (id) => `/api/v1/assessments/${id}`,
      providesTags: (result, error, id) => [{ type: 'Assessment', id }],
    }),

    createAssessment: builder.mutation<Assessment, Partial<Assessment>>({
      query: (data) => {
        // Transform camelCase to snake_case for backend
        const transformedData: any = {};
        if (data.title !== undefined) transformedData.title = data.title;
        if (data.lessonId !== undefined) transformedData.lesson_id = data.lessonId;
        if (data.classId !== undefined) transformedData.class_id = data.classId;
        if (data.type !== undefined) transformedData.type = data.type;
        transformedData.questions = data.questions || [];
        if (data.dueDate !== undefined) transformedData.due_date = data.dueDate;
        if (data.maxSubmissions !== undefined) transformedData.max_attempts = data.maxSubmissions;
        if (data.status !== undefined) transformedData.status = data.status;

        return {
          url: '/api/v1/assessments/',
          method: 'POST',
          body: transformedData,
        };
      },
      invalidatesTags: [{ type: 'Assessment', id: 'LIST' }],
    }),

    updateAssessment: builder.mutation<Assessment, { id: string; data: Partial<Assessment> }>({
      query: ({ id, data }) => ({
        url: `/api/v1/assessments/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Assessment', id },
        { type: 'Assessment', id: 'LIST' },
      ],
    }),

    deleteAssessment: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/v1/assessments/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Assessment', id },
        { type: 'Assessment', id: 'LIST' },
      ],
    }),

    publishAssessment: builder.mutation<Assessment, string>({
      query: (id) => ({
        url: `/api/v1/assessments/${id}/publish`,
        method: 'PUT',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Assessment', id },
        { type: 'Assessment', id: 'LIST' },
      ],
    }),

    submitAssessment: builder.mutation<AssessmentSubmission, {
      assessmentId: string;
      data: { answers: any; time_spent_minutes?: number };
    }>({
      query: ({ assessmentId, data }) => ({
        url: `/assessments/${assessmentId}/submit`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: (result, error, { assessmentId }) => [
        { type: 'Assessment', id: assessmentId },
        'Progress',
      ],
    }),

    // Messages endpoints
    getMessages: builder.query<Message[], {
      folder?: string;
      unread_only?: boolean;
      class_id?: string;
      search?: string;
    }>({
      query: (params) => ({
        url: '/api/v1/messages/',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Message' as const, id })),
              { type: 'Message', id: 'LIST' },
            ]
          : [{ type: 'Message', id: 'LIST' }],
    }),

    getMessage: builder.query<Message, string>({
      query: (id) => `/api/v1/messages/${id}`,
      providesTags: (result, error, id) => [{ type: 'Message', id }],
    }),

    sendMessage: builder.mutation<Message, {
      subject: string;
      body: string;
      recipient_ids: string[];
      class_id?: string;
      priority?: string;
    }>({
      query: (data) => ({
        url: '/api/v1/messages/',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [{ type: 'Message', id: 'LIST' }],
      // Optimistic update for sent messages
      async onQueryStarted(newMessage, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          api.util.updateQueryData('getMessages', {}, (draft) => {
            const optimisticMessage = {
              id: `temp-${Date.now()}`,
              subject: newMessage.subject,
              body: newMessage.body,
              sender_id: 'current-user', // Would be filled from auth state
              recipient_ids: newMessage.recipient_ids,
              class_id: newMessage.class_id,
              priority: newMessage.priority || 'normal',
              is_read: true,
              is_starred: false,
              is_archived: false,
              folder: 'sent',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            } as Message;

            draft.unshift(optimisticMessage);
          })
        );

        try {
          const { data: actualMessage } = await queryFulfilled;
          dispatch(
            api.util.updateQueryData('getMessages', {}, (draft) => {
              const index = draft.findIndex(m => m.id.startsWith('temp-'));
              if (index !== -1) {
                draft[index] = actualMessage;
              }
            })
          );
        } catch {
          patchResult.undo();
        }
      },
    }),

    markMessageAsRead: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/v1/messages/${id}/read`,
        method: 'PUT',
      }),
      invalidatesTags: (result, error, id) => [{ type: 'Message', id }],
      // Optimistic update
      async onQueryStarted(id, { dispatch, queryFulfilled }) {
        const patchResults = [
          dispatch(
            api.util.updateQueryData('getMessages', {}, (draft) => {
              const message = draft.find(m => m.id === id);
              if (message) {
                message.is_read = true;
              }
            })
          ),
          dispatch(
            api.util.updateQueryData('getMessage', id, (draft) => {
              if (draft) {
                draft.is_read = true;
              }
            })
          ),
        ];

        try {
          await queryFulfilled;
        } catch {
          patchResults.forEach(patch => patch.undo());
        }
      },
    }),

    deleteMessage: builder.mutation<void, { id: string; permanent?: boolean }>({
      query: ({ id, permanent }) => ({
        url: `/api/v1/messages/${id}`,
        method: 'DELETE',
        params: permanent ? { permanent } : undefined,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Message', id },
        { type: 'Message', id: 'LIST' },
      ],
    }),

    // Analytics endpoints
    getWeeklyXP: builder.query<ProgressPoint[], string | void>({
      query: (studentId) => ({
        url: '/api/v1/analytics/weekly_xp',
        params: studentId ? { studentId } : undefined,
      }),
      providesTags: ['Analytics'],
    }),

    getSubjectMastery: builder.query<{ subject: string; mastery: number }[], string | void>({
      query: (studentId) => ({
        url: '/api/v1/analytics/subject_mastery',
        params: studentId ? { studentId } : undefined,
      }),
      providesTags: ['Analytics'],
    }),

    // Progress endpoints
    getStudentProgress: builder.query<StudentProgress, string>({
      query: (studentId) => `/api/v1/progress/student/${studentId}`,
      providesTags: (result, error, studentId) => [{ type: 'Progress', id: studentId }],
    }),

    updateProgress: builder.mutation<any, {
      lessonId: string;
      progressPercentage: number;
      timeSpentMinutes: number;
      score?: number;
    }>({
      query: (data) => ({
        url: '/api/v1/progress/update',
        method: 'POST',
        body: {
          lesson_id: data.lessonId,
          progress_percentage: data.progressPercentage,
          time_spent_minutes: data.timeSpentMinutes,
          score: data.score,
        },
      }),
      invalidatesTags: ['Progress', 'Dashboard', 'Analytics'],
    }),

    // Gamification endpoints
    getBadges: builder.query<Badge[], string | void>({
      query: (studentId) => ({
        url: '/api/v1/gamification/badges',
        params: studentId ? { studentId } : undefined,
      }),
      providesTags: ['Badge'],
    }),

    getLeaderboard: builder.query<LeaderboardEntry[], {
      classId?: string;
      timeframe?: 'daily' | 'weekly' | 'monthly' | 'all';
    }>({
      query: (params) => ({
        url: '/api/v1/gamification/leaderboard',
        params,
      }),
      providesTags: ['Leaderboard'],
    }),

    addXP: builder.mutation<XPTransaction, {
      studentId: string;
      amount: number;
      reason: string;
    }>({
      query: ({ studentId, amount, reason }) => ({
        url: `/api/v1/gamification/xp/${studentId}`,
        method: 'POST',
        body: { amount, reason },
      }),
      invalidatesTags: ['Leaderboard', 'Progress', 'Dashboard'],
    }),

    // Compliance endpoints
    getComplianceStatus: builder.query<ComplianceStatus, void>({
      query: () => '/api/v1/analytics/compliance/status',
      providesTags: ['Compliance'],
    }),

    recordConsent: builder.mutation<void, {
      type: 'coppa' | 'ferpa' | 'gdpr';
      userId: string;
    }>({
      query: ({ type, userId }) => ({
        url: '/api/v1/compliance/consent',
        method: 'POST',
        body: {
          consent_type: type,
          granted: true,
          details: {
            userId,
            timestamp: new Date().toISOString(),
          },
        },
      }),
      invalidatesTags: ['Compliance'],
    }),

    // Roblox endpoints
    getRobloxWorlds: builder.query<RobloxWorld[], string | void>({
      query: (lessonId) => ({
        url: '/api/v1/roblox/worlds',
        params: lessonId ? { lessonId } : undefined,
      }),
      providesTags: ['RobloxWorld'],
    }),

    pushLessonToRoblox: builder.mutation<{ jobId: string; status: string }, string>({
      query: (lessonId) => ({
        url: `/api/v1/roblox/push/${lessonId}`,
        method: 'POST',
      }),
      invalidatesTags: ['RobloxWorld'],
    }),

    // User management endpoints
    getUsers: builder.query<User[], {
      skip?: number;
      limit?: number;
      role?: string;
      school_id?: string;
      is_active?: boolean;
      search?: string;
    }>({
      query: (params) => ({
        url: '/api/v1/users/',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'User' as const, id })),
              { type: 'User', id: 'LIST' },
            ]
          : [{ type: 'User', id: 'LIST' }],
    }),

    getUser: builder.query<User, string>({
      query: (id) => `/api/v1/users/${id}`,
      providesTags: (result, error, id) => [{ type: 'User', id }],
    }),

    createUser: builder.mutation<User, UserCreate>({
      query: (data) => {
        const transformedData = {
          email: data.email,
          username: data.username,
          password: data.password,
          first_name: data.firstName,
          last_name: data.lastName,
          display_name: data.displayName,
          role: data.role,
          school_id: data.schoolId,
          language: data.language,
          timezone: data.timezone,
        };

        return {
          url: '/api/v1/users/',
          method: 'POST',
          body: transformedData,
        };
      },
      invalidatesTags: [{ type: 'User', id: 'LIST' }],
    }),

    updateUser: builder.mutation<User, { id: string; data: UserUpdate }>({
      query: ({ id, data }) => {
        const transformedData: any = {};
        if (data.email !== undefined) transformedData.email = data.email;
        if (data.username !== undefined) transformedData.username = data.username;
        if (data.password !== undefined) transformedData.password = data.password;
        if (data.firstName !== undefined) transformedData.first_name = data.firstName;
        if (data.lastName !== undefined) transformedData.last_name = data.lastName;
        if (data.displayName !== undefined) transformedData.display_name = data.displayName;
        if (data.role !== undefined) transformedData.role = data.role;
        if (data.schoolId !== undefined) transformedData.school_id = data.schoolId;
        if (data.isActive !== undefined) transformedData.is_active = data.isActive;

        return {
          url: `/api/v1/users/${id}`,
          method: 'PUT',
          body: transformedData,
        };
      },
      invalidatesTags: (result, error, { id }) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    deleteUser: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/v1/users/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'User', id },
        { type: 'User', id: 'LIST' },
      ],
    }),

    // Realtime trigger helper
    triggerRealtime: builder.mutation<any, {
      channel: string;
      event?: string;
      type?: string;
      payload?: any;
    }>({
      query: (data) => ({
        url: '/realtime/trigger',
        method: 'POST',
        body: data,
      }),
      // Don't show error notifications for realtime failures
      extraOptions: {
        silentError: true,
      },
    }),
  }),
});

// Export hooks for usage in functional components
export const {
  // Dashboard
  useGetDashboardOverviewQuery,
  useLazyGetDashboardOverviewQuery,

  // Authentication
  useLoginMutation,
  useRegisterMutation,
  useRefreshTokenMutation,
  useLogoutMutation,

  // Classes
  useGetClassesQuery,
  useLazyGetClassesQuery,
  useGetClassQuery,
  useCreateClassMutation,
  useUpdateClassMutation,
  useDeleteClassMutation,

  // Lessons
  useGetLessonsQuery,
  useGetLessonQuery,
  useCreateLessonMutation,
  useUpdateLessonMutation,
  useDeleteLessonMutation,

  // Assessments
  useGetAssessmentsQuery,
  useGetAssessmentQuery,
  useCreateAssessmentMutation,
  useUpdateAssessmentMutation,
  useDeleteAssessmentMutation,
  usePublishAssessmentMutation,
  useSubmitAssessmentMutation,

  // Messages
  useGetMessagesQuery,
  useGetMessageQuery,
  useSendMessageMutation,
  useMarkMessageAsReadMutation,
  useDeleteMessageMutation,

  // Analytics
  useGetWeeklyXPQuery,
  useGetSubjectMasteryQuery,

  // Progress
  useGetStudentProgressQuery,
  useUpdateProgressMutation,

  // Gamification
  useGetBadgesQuery,
  useGetLeaderboardQuery,
  useAddXPMutation,

  // Compliance
  useGetComplianceStatusQuery,
  useRecordConsentMutation,

  // Roblox
  useGetRobloxWorldsQuery,
  usePushLessonToRobloxMutation,

  // Users
  useGetUsersQuery,
  useGetUserQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,

  // Realtime
  useTriggerRealtimeMutation,
} = api;

export default api;