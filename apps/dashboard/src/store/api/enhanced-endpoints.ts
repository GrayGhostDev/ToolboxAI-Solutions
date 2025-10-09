/**
 * Enhanced RTK Query Endpoints with Type Safety and Zod Validation
 *
 * This file provides type-safe API endpoints with runtime validation using Zod schemas.
 * All API responses are validated at runtime to ensure type safety.
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError } from '@reduxjs/toolkit/query';
import { z } from 'zod';
import { type RootState } from '../index';
import { addNotification } from '../slices/uiSlice';
import {
  API_BASE_URL,
  AUTH_TOKEN_KEY,
} from '../../config';

// Import our Zod schemas
import {
  UserSchema,
  AuthResponseSchema,
  DashboardOverviewSchema,
  ClassSummarySchema,
  ClassDetailsSchema,
  LessonSchema,
  AssessmentSchema,
  StudentProgressSchema,
  LeaderboardEntrySchema,
  BadgeSchema,
  XPTransactionSchema,
  NotificationSchema,
  MessageSchema,
  RobloxWorldSchema,
  ApiResponseSchema,
  validateApiResponse,
} from '../../types/schemas';

import type {
  UserId,
  ClassId,
  LessonId,
  AssessmentId,
  createUserId,
  createClassId,
  createLessonId,
  createAssessmentId,
} from '../../types/branded';

import type {
  DataState,
  LoadingState,
  createDataState,
} from '../../types/discriminated-unions';

// Enhanced base query with validation
const baseQueryWithValidation: BaseQueryFn<
  string | (FetchArgs & { schema?: z.ZodSchema<any> }),
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

  const result = await baseQuery(args, api, extraOptions);

  // Runtime validation if schema is provided
  if (typeof args === 'object' && 'schema' in args && args.schema && result.data) {
    try {
      const validationResult = validateApiResponse(args.schema, result.data);
      if (!validationResult.success) {
        console.error('API Response Validation Failed:', validationResult.error);

        // In development, throw an error for validation failures
        if (process.env.NODE_ENV === 'development') {
          return {
            error: {
              status: 'CUSTOM_ERROR' as const,
              error: `API response validation failed: ${validationResult.error}`,
              data: result.data,
            } as FetchBaseQueryError,
            data: undefined,
          };
        }

        // In production, log the error but continue
        api.dispatch(addNotification({
          id: Date.now().toString(),
          type: 'warning',
          message: 'Data validation warning - please refresh the page',
          timestamp: Date.now(),
          autoHide: true,
        }));
      } else {
        result.data = validationResult.data;
      }
    } catch (error) {
      console.error('Schema validation error:', error);
    }
  }

  return result;
};

// Create the enhanced API
export const enhancedApi = createApi({
  reducerPath: 'enhancedApi',
  baseQuery: baseQueryWithValidation,
  tagTypes: [
    'User',
    'Class',
    'Lesson',
    'Assessment',
    'Student',
    'Progress',
    'Badge',
    'Leaderboard',
    'Notification',
    'Message',
    'RobloxWorld',
    'Dashboard',
  ],
  endpoints: (builder) => ({
    // User endpoints
    getCurrentUser: builder.query<z.infer<typeof UserSchema>, void>({
      query: () => ({
        url: '/api/v1/users/me',
        schema: UserSchema,
      }),
      providesTags: ['User'],
    }),

    updateUser: builder.mutation<
      z.infer<typeof UserSchema>,
      { userId: UserId; updates: Partial<z.infer<typeof UserSchema>> }
    >({
      query: ({ userId, updates }) => ({
        url: `/api/v1/users/${userId}`,
        method: 'PATCH',
        body: updates,
        schema: UserSchema,
      }),
      invalidatesTags: ['User'],
    }),

    // Authentication endpoints
    login: builder.mutation<
      z.infer<typeof AuthResponseSchema>,
      { email: string; password: string }
    >({
      query: (credentials) => ({
        url: '/api/v1/auth/login',
        method: 'POST',
        body: credentials,
        schema: AuthResponseSchema,
      }),
      invalidatesTags: ['User', 'Dashboard'],
    }),

    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/api/v1/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User', 'Dashboard'],
    }),

    // Dashboard endpoints
    getDashboardOverview: builder.query<z.infer<typeof DashboardOverviewSchema>, void>({
      query: () => ({
        url: '/api/v1/dashboard/overview',
        schema: DashboardOverviewSchema,
      }),
      providesTags: ['Dashboard'],
    }),

    // Class endpoints
    getClasses: builder.query<z.infer<typeof ClassSummarySchema>[], void>({
      query: () => ({
        url: '/api/v1/classes',
        schema: z.array(ClassSummarySchema),
      }),
      providesTags: ['Class'],
    }),

    getClass: builder.query<z.infer<typeof ClassDetailsSchema>, ClassId>({
      query: (classId) => ({
        url: `/api/v1/classes/${classId}`,
        schema: ClassDetailsSchema,
      }),
      providesTags: (result, error, classId) => [{ type: 'Class', id: classId }],
    }),

    createClass: builder.mutation<
      z.infer<typeof ClassSummarySchema>,
      { name: string; grade: number; description?: string }
    >({
      query: (classData) => ({
        url: '/api/v1/classes',
        method: 'POST',
        body: classData,
        schema: ClassSummarySchema,
      }),
      invalidatesTags: ['Class'],
    }),

    updateClass: builder.mutation<
      z.infer<typeof ClassSummarySchema>,
      { classId: ClassId; updates: Partial<z.infer<typeof ClassSummarySchema>> }
    >({
      query: ({ classId, updates }) => ({
        url: `/api/v1/classes/${classId}`,
        method: 'PATCH',
        body: updates,
        schema: ClassSummarySchema,
      }),
      invalidatesTags: (result, error, { classId }) => [
        { type: 'Class', id: classId },
        'Class',
      ],
    }),

    deleteClass: builder.mutation<void, ClassId>({
      query: (classId) => ({
        url: `/api/v1/classes/${classId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Class'],
    }),

    // Lesson endpoints
    getLessons: builder.query<
      z.infer<typeof LessonSchema>[],
      { classId?: ClassId; subject?: string; limit?: number }
    >({
      query: (params) => {
        const searchParams = new URLSearchParams();
        if (params.classId) searchParams.append('classId', params.classId);
        if (params.subject) searchParams.append('subject', params.subject);
        if (params.limit) searchParams.append('limit', params.limit.toString());

        return {
          url: `/api/v1/lessons?${searchParams.toString()}`,
          schema: z.array(LessonSchema),
        };
      },
      providesTags: ['Lesson'],
    }),

    getLesson: builder.query<z.infer<typeof LessonSchema>, LessonId>({
      query: (lessonId) => ({
        url: `/api/v1/lessons/${lessonId}`,
        schema: LessonSchema,
      }),
      providesTags: (result, error, lessonId) => [{ type: 'Lesson', id: lessonId }],
    }),

    createLesson: builder.mutation<
      z.infer<typeof LessonSchema>,
      {
        title: string;
        description: string;
        subject: string;
        classIds: ClassId[];
        content: unknown;
      }
    >({
      query: (lessonData) => ({
        url: '/api/v1/lessons',
        method: 'POST',
        body: lessonData,
        schema: LessonSchema,
      }),
      invalidatesTags: ['Lesson', 'Class'],
    }),

    // Assessment endpoints
    getAssessments: builder.query<
      z.infer<typeof AssessmentSchema>[],
      { classId?: ClassId; lessonId?: LessonId; status?: string }
    >({
      query: (params) => {
        const searchParams = new URLSearchParams();
        if (params.classId) searchParams.append('classId', params.classId);
        if (params.lessonId) searchParams.append('lessonId', params.lessonId);
        if (params.status) searchParams.append('status', params.status);

        return {
          url: `/api/v1/assessments?${searchParams.toString()}`,
          schema: z.array(AssessmentSchema),
        };
      },
      providesTags: ['Assessment'],
    }),

    getAssessment: builder.query<z.infer<typeof AssessmentSchema>, AssessmentId>({
      query: (assessmentId) => ({
        url: `/api/v1/assessments/${assessmentId}`,
        schema: AssessmentSchema,
      }),
      providesTags: (result, error, assessmentId) => [
        { type: 'Assessment', id: assessmentId },
      ],
    }),

    // Student Progress endpoints
    getStudentProgress: builder.query<
      z.infer<typeof StudentProgressSchema>,
      { studentId: UserId; timeRange?: 'week' | 'month' | 'quarter' | 'year' }
    >({
      query: ({ studentId, timeRange = 'month' }) => ({
        url: `/api/v1/students/${studentId}/progress?timeRange=${timeRange}`,
        schema: StudentProgressSchema,
      }),
      providesTags: (result, error, { studentId }) => [
        { type: 'Progress', id: studentId },
      ],
    }),

    // Gamification endpoints
    getLeaderboard: builder.query<
      z.infer<typeof LeaderboardEntrySchema>[],
      { scope: 'class' | 'school' | 'global'; classId?: ClassId; limit?: number }
    >({
      query: ({ scope, classId, limit = 50 }) => {
        const searchParams = new URLSearchParams();
        searchParams.append('scope', scope);
        if (classId) searchParams.append('classId', classId);
        searchParams.append('limit', limit.toString());

        return {
          url: `/api/v1/gamification/leaderboard?${searchParams.toString()}`,
          schema: z.array(LeaderboardEntrySchema),
        };
      },
      providesTags: ['Leaderboard'],
    }),

    getBadges: builder.query<
      z.infer<typeof BadgeSchema>[],
      { studentId?: UserId; category?: string; earned?: boolean }
    >({
      query: (params) => {
        const searchParams = new URLSearchParams();
        if (params.studentId) searchParams.append('studentId', params.studentId);
        if (params.category) searchParams.append('category', params.category);
        if (params.earned !== undefined) searchParams.append('earned', params.earned.toString());

        return {
          url: `/api/v1/gamification/badges?${searchParams.toString()}`,
          schema: z.array(BadgeSchema),
        };
      },
      providesTags: ['Badge'],
    }),

    getXPTransactions: builder.query<
      z.infer<typeof XPTransactionSchema>[],
      { studentId: UserId; limit?: number; source?: string }
    >({
      query: ({ studentId, limit = 20, source }) => {
        const searchParams = new URLSearchParams();
        searchParams.append('limit', limit.toString());
        if (source) searchParams.append('source', source);

        return {
          url: `/api/v1/students/${studentId}/xp-transactions?${searchParams.toString()}`,
          schema: z.array(XPTransactionSchema),
        };
      },
      providesTags: (result, error, { studentId }) => [
        { type: 'Progress', id: studentId },
      ],
    }),

    // Notification endpoints
    getNotifications: builder.query<
      z.infer<typeof NotificationSchema>[],
      { read?: boolean; type?: string; limit?: number }
    >({
      query: (params) => {
        const searchParams = new URLSearchParams();
        if (params.read !== undefined) searchParams.append('read', params.read.toString());
        if (params.type) searchParams.append('type', params.type);
        if (params.limit) searchParams.append('limit', params.limit.toString());

        return {
          url: `/api/v1/notifications?${searchParams.toString()}`,
          schema: z.array(NotificationSchema),
        };
      },
      providesTags: ['Notification'],
    }),

    markNotificationAsRead: builder.mutation<void, string>({
      query: (notificationId) => ({
        url: `/api/v1/notifications/${notificationId}/read`,
        method: 'PATCH',
      }),
      invalidatesTags: ['Notification'],
    }),

    // Message endpoints
    getMessages: builder.query<
      z.infer<typeof MessageSchema>[],
      { folder?: 'inbox' | 'sent' | 'drafts'; limit?: number }
    >({
      query: ({ folder = 'inbox', limit = 20 }) => ({
        url: `/api/v1/messages?folder=${folder}&limit=${limit}`,
        schema: z.array(MessageSchema),
      }),
      providesTags: ['Message'],
    }),

    sendMessage: builder.mutation<
      z.infer<typeof MessageSchema>,
      { toUserId: UserId; subject: string; content: string; attachments?: string[] }
    >({
      query: (messageData) => ({
        url: '/api/v1/messages',
        method: 'POST',
        body: messageData,
        schema: MessageSchema,
      }),
      invalidatesTags: ['Message'],
    }),

    // Roblox World endpoints
    getRobloxWorlds: builder.query<
      z.infer<typeof RobloxWorldSchema>[],
      { lessonId?: LessonId; status?: string; limit?: number }
    >({
      query: (params) => {
        const searchParams = new URLSearchParams();
        if (params.lessonId) searchParams.append('lessonId', params.lessonId);
        if (params.status) searchParams.append('status', params.status);
        if (params.limit) searchParams.append('limit', params.limit.toString());

        return {
          url: `/api/v1/roblox/worlds?${searchParams.toString()}`,
          schema: z.array(RobloxWorldSchema),
        };
      },
      providesTags: ['RobloxWorld'],
    }),

    getRobloxWorld: builder.query<z.infer<typeof RobloxWorldSchema>, string>({
      query: (worldId) => ({
        url: `/api/v1/roblox/worlds/${worldId}`,
        schema: RobloxWorldSchema,
      }),
      providesTags: (result, error, worldId) => [{ type: 'RobloxWorld', id: worldId }],
    }),

    joinRobloxWorld: builder.mutation<{ joinUrl: string }, string>({
      query: (worldId) => ({
        url: `/api/v1/roblox/worlds/${worldId}/join`,
        method: 'POST',
        schema: z.object({ joinUrl: z.string().url() }),
      }),
    }),
  }),
});

// Export hooks with proper typing
export const {
  // User hooks
  useGetCurrentUserQuery,
  useUpdateUserMutation,

  // Auth hooks
  useLoginMutation,
  useLogoutMutation,

  // Dashboard hooks
  useGetDashboardOverviewQuery,

  // Class hooks
  useGetClassesQuery,
  useGetClassQuery,
  useCreateClassMutation,
  useUpdateClassMutation,
  useDeleteClassMutation,

  // Lesson hooks
  useGetLessonsQuery,
  useGetLessonQuery,
  useCreateLessonMutation,

  // Assessment hooks
  useGetAssessmentsQuery,
  useGetAssessmentQuery,

  // Progress hooks
  useGetStudentProgressQuery,

  // Gamification hooks
  useGetLeaderboardQuery,
  useGetBadgesQuery,
  useGetXPTransactionsQuery,

  // Notification hooks
  useGetNotificationsQuery,
  useMarkNotificationAsReadMutation,

  // Message hooks
  useGetMessagesQuery,
  useSendMessageMutation,

  // Roblox hooks
  useGetRobloxWorldsQuery,
  useGetRobloxWorldQuery,
  useJoinRobloxWorldMutation,
} = enhancedApi;

// Enhanced selectors with type safety
export const selectCurrentUser = (state: RootState) =>
  state.enhancedApi.queries['getCurrentUser(undefined)']?.data;

export const selectUserDataState = (state: RootState): DataState<z.infer<typeof UserSchema>> => {
  const queryState = state.enhancedApi.queries['getCurrentUser(undefined)'];

  if (!queryState) {
    return createDataState.idle();
  }

  if (queryState.status === 'pending') {
    return createDataState.loading();
  }

  if (queryState.status === 'fulfilled' && queryState.data) {
    return createDataState.succeeded(
      queryState.data,
      new Date(queryState.fulfilledTimeStamp).toISOString() as any
    );
  }

  if (queryState.status === 'rejected') {
    return createDataState.failed(
      queryState.error?.toString() || 'Unknown error',
      new Date().toISOString() as any
    );
  }

  return createDataState.idle();
};

// Type-safe cache selectors
export const selectClassById = (classId: ClassId) => (state: RootState) =>
  state.enhancedApi.queries[`getClass("${classId}")`]?.data;

export const selectLessonById = (lessonId: LessonId) => (state: RootState) =>
  state.enhancedApi.queries[`getLesson("${lessonId}")`]?.data;

export const selectAssessmentById = (assessmentId: AssessmentId) => (state: RootState) =>
  state.enhancedApi.queries[`getAssessment("${assessmentId}")`]?.data;

// Optimistic update helpers
export const optimisticUpdateUser = (
  userId: UserId,
  updates: Partial<z.infer<typeof UserSchema>>
) => {
  return enhancedApi.util.updateQueryData('getCurrentUser', undefined, (draft) => {
    if (draft && draft.id === userId) {
      Object.assign(draft, updates);
    }
  });
};

export const optimisticUpdateClass = (
  classId: ClassId,
  updates: Partial<z.infer<typeof ClassDetailsSchema>>
) => {
  return enhancedApi.util.updateQueryData('getClass', classId, (draft) => {
    Object.assign(draft, updates);
  });
};

// Cache invalidation helpers
export const invalidateUserCache = () => enhancedApi.util.invalidateTags(['User']);
export const invalidateClassCache = () => enhancedApi.util.invalidateTags(['Class']);
export const invalidateLessonCache = () => enhancedApi.util.invalidateTags(['Lesson']);
export const invalidateProgressCache = () => enhancedApi.util.invalidateTags(['Progress']);

// Prefetch helpers
export const prefetchDashboard = () => enhancedApi.util.prefetch('getDashboardOverview', undefined);
export const prefetchClasses = () => enhancedApi.util.prefetch('getClasses', undefined);
export const prefetchLeaderboard = (scope: 'class' | 'school' | 'global', classId?: ClassId) =>
  enhancedApi.util.prefetch('getLeaderboard', { scope, classId });

export default enhancedApi;