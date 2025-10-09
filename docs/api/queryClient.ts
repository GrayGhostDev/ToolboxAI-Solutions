import { QueryClient } from '@tanstack/react-query';

/**
 * React Query Client Configuration
 *
 * Centralized configuration for React Query (TanStack Query).
 * Handles server state management, caching, and data fetching.
 *
 * Official docs: https://tanstack.com/query/latest
 *
 * Features:
 * - Smart caching with staleTime
 * - Automatic retries with exponential backoff
 * - Background refetching
 * - Optimistic updates
 * - DevTools integration
 */

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: how long data is considered fresh (5 minutes)
      staleTime: 5 * 60 * 1000,

      // Cache time: how long inactive data stays in cache (10 minutes)
      gcTime: 10 * 60 * 1000,

      // Retry failed requests
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        if (error instanceof Error && 'status' in error) {
          const status = (error as any).status;
          if (status >= 400 && status < 500) {
            return false;
          }
        }
        // Retry up to 3 times for other errors
        return failureCount < 3;
      },

      // Retry delay with exponential backoff
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Refetch on window focus
      refetchOnWindowFocus: true,

      // Refetch on reconnect
      refetchOnReconnect: true,

      // Don't refetch on mount if data is fresh
      refetchOnMount: false,

      // Network mode
      networkMode: 'online',
    },
    mutations: {
      // Retry mutations
      retry: 1,

      // Network mode for mutations
      networkMode: 'online',
    },
  },
});

/**
 * Query keys factory
 *
 * Centralized query key management for consistency and type safety.
 *
 * @example
 * ```tsx
 * const userQuery = useQuery({
 *   queryKey: queryKeys.user(userId),
 *   queryFn: () => fetchUser(userId)
 * });
 * ```
 */
export const queryKeys = {
  // User queries
  user: (id: string) => ['user', id] as const,
  users: () => ['users'] as const,
  userProfile: (id: string) => ['user', id, 'profile'] as const,

  // Dashboard queries
  dashboard: () => ['dashboard'] as const,
  dashboardStats: () => ['dashboard', 'stats'] as const,
  dashboardWidgets: () => ['dashboard', 'widgets'] as const,

  // Classes queries
  classes: () => ['classes'] as const,
  class: (id: string) => ['class', id] as const,
  classStudents: (id: string) => ['class', id, 'students'] as const,

  // Lessons queries
  lessons: () => ['lessons'] as const,
  lesson: (id: string) => ['lesson', id] as const,
  lessonContent: (id: string) => ['lesson', id, 'content'] as const,

  // Analytics queries
  analytics: () => ['analytics'] as const,
  analyticsRange: (start: Date, end: Date) =>
    ['analytics', start.toISOString(), end.toISOString()] as const,

  // Roblox queries
  roblox: () => ['roblox'] as const,
  robloxEnvironment: () => ['roblox', 'environment'] as const,
  robloxSync: () => ['roblox', 'sync'] as const,
} as const;

/**
 * Example hook using React Query
 *
 * @example
 * ```tsx
 * import { useQuery } from '@tanstack/react-query';
 * import { queryKeys } from '@/api/queryClient';
 * import { fetchUser } from '@/api/users';
 *
 * export function useUser(userId: string) {
 *   return useQuery({
 *     queryKey: queryKeys.user(userId),
 *     queryFn: () => fetchUser(userId),
 *     enabled: !!userId, // Only fetch if userId exists
 *   });
 * }
 *
 * // Usage in component
 * function UserProfile({ userId }: { userId: string }) {
 *   const { data: user, isLoading, error } = useUser(userId);
 *
 *   if (isLoading) return <Loader />;
 *   if (error) return <Alert color="red">Error loading user</Alert>;
 *   if (!user) return null;
 *
 *   return <div>{user.name}</div>;
 * }
 * ```
 */

/**
 * Mutation example
 *
 * @example
 * ```tsx
 * import { useMutation, useQueryClient } from '@tanstack/react-query';
 * import { queryKeys } from '@/api/queryClient';
 * import { updateUser } from '@/api/users';
 *
 * export function useUpdateUser() {
 *   const queryClient = useQueryClient();
 *
 *   return useMutation({
 *     mutationFn: updateUser,
 *     onSuccess: (updatedUser) => {
 *       // Invalidate and refetch
 *       queryClient.invalidateQueries({
 *         queryKey: queryKeys.user(updatedUser.id)
 *       });
 *     },
 *     // Optimistic update
 *     onMutate: async (newUser) => {
 *       await queryClient.cancelQueries({
 *         queryKey: queryKeys.user(newUser.id)
 *       });
 *
 *       const previousUser = queryClient.getQueryData(
 *         queryKeys.user(newUser.id)
 *       );
 *
 *       queryClient.setQueryData(queryKeys.user(newUser.id), newUser);
 *
 *       return { previousUser };
 *     },
 *     onError: (err, newUser, context) => {
 *       // Rollback on error
 *       if (context?.previousUser) {
 *         queryClient.setQueryData(
 *           queryKeys.user(newUser.id),
 *           context.previousUser
 *         );
 *       }
 *     },
 *   });
 * }
 * ```
 */

/**
 * Infinite query example (pagination)
 *
 * @example
 * ```tsx
 * import { useInfiniteQuery } from '@tanstack/react-query';
 *
 * function useInfiniteLessons() {
 *   return useInfiniteQuery({
 *     queryKey: queryKeys.lessons(),
 *     queryFn: ({ pageParam = 0 }) => fetchLessons(pageParam),
 *     getNextPageParam: (lastPage, pages) => {
 *       return lastPage.hasMore ? pages.length : undefined;
 *     },
 *     initialPageParam: 0,
 *   });
 * }
 *
 * // Usage
 * function LessonList() {
 *   const {
 *     data,
 *     fetchNextPage,
 *     hasNextPage,
 *     isFetchingNextPage,
 *   } = useInfiniteLessons();
 *
 *   return (
 *     <div>
 *       {data?.pages.map((page) =>
 *         page.lessons.map((lesson) => (
 *           <div key={lesson.id}>{lesson.title}</div>
 *         ))
 *       )}
 *       {hasNextPage && (
 *         <Button onClick={() => fetchNextPage()} loading={isFetchingNextPage}>
 *           Load More
 *         </Button>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
