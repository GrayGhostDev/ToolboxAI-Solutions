/**
 * Template Literal Types for Type-Safe Routing
 *
 * These types provide compile-time safety for route construction and navigation,
 * preventing typos and ensuring parameter types are correct.
 */

import type { UserId, ClassId, LessonId, AssessmentId, MessageId } from './branded';

// Base route definitions
export type BaseRoutes = {
  '/': {};
  '/login': {};
  '/register': {};
  '/password-reset': {};
  '/dashboard': {};
  '/profile': {};
  '/settings': {};
  '/help': {};
  '/privacy': {};
  '/terms': {};
};

// Parameterized route definitions
export type ParameterizedRoutes = {
  '/dashboard/classes/:classId': { classId: ClassId };
  '/dashboard/classes/:classId/students': { classId: ClassId };
  '/dashboard/classes/:classId/lessons': { classId: ClassId };
  '/dashboard/classes/:classId/assessments': { classId: ClassId };
  '/dashboard/lessons/:lessonId': { lessonId: LessonId };
  '/dashboard/lessons/:lessonId/edit': { lessonId: LessonId };
  '/dashboard/assessments/:assessmentId': { assessmentId: AssessmentId };
  '/dashboard/assessments/:assessmentId/take': { assessmentId: AssessmentId };
  '/dashboard/assessments/:assessmentId/results': { assessmentId: AssessmentId };
  '/dashboard/users/:userId': { userId: UserId };
  '/dashboard/users/:userId/edit': { userId: UserId };
  '/dashboard/messages/:messageId': { messageId: MessageId };
  '/dashboard/roblox/worlds/:worldId': { worldId: string };
  '/dashboard/roblox/worlds/:worldId/join': { worldId: string };
};

// Query parameter types
export type QueryParams = {
  // Pagination
  page?: number;
  limit?: number;

  // Sorting
  sortBy?: string;
  sortDir?: 'asc' | 'desc';

  // Filtering
  status?: 'active' | 'inactive' | 'archived' | 'draft' | 'published';
  subject?: 'Math' | 'Science' | 'Language' | 'Arts' | 'Technology' | 'Social Studies' | 'Physical Education' | 'Life Skills';
  grade?: number;
  role?: 'admin' | 'teacher' | 'student' | 'parent';

  // Search
  search?: string;

  // Date ranges
  startDate?: string;
  endDate?: string;

  // Dashboard specific
  timeRange?: 'day' | 'week' | 'month' | 'quarter' | 'year';
  metric?: 'progress' | 'engagement' | 'performance' | 'compliance';

  // Assessment specific
  attemptId?: string;
  showAnswers?: boolean;

  // Class specific
  includeArchived?: boolean;

  // Message specific
  folder?: 'inbox' | 'sent' | 'drafts' | 'trash';

  // Notification specific
  type?: 'info' | 'warning' | 'success' | 'error';
  read?: boolean;

  // Gamification specific
  leaderboardType?: 'class' | 'school' | 'global';
  badgeCategory?: 'achievement' | 'milestone' | 'special' | 'seasonal';

  // Roblox specific
  worldStatus?: 'draft' | 'published' | 'archived';
  difficulty?: 'easy' | 'medium' | 'hard';
};

// All route types combined
export type AllRoutes = BaseRoutes & ParameterizedRoutes;

// Extract route keys
export type RoutePath = keyof AllRoutes;

// Extract parameters for a specific route
export type RouteParams<T extends RoutePath> = AllRoutes[T];

// Helper type to check if route has parameters
export type HasParams<T extends RoutePath> = keyof RouteParams<T> extends never ? false : true;

// Extract parameter names from route string
type ExtractParams<T extends string> = T extends `${string}:${infer Param}/${infer Rest}`
  ? Param | ExtractParams<Rest>
  : T extends `${string}:${infer Param}`
  ? Param
  : never;

// Build URL with parameters
export type BuildUrl<T extends RoutePath> = HasParams<T> extends true
  ? (params: RouteParams<T>, query?: QueryParams) => string
  : (query?: QueryParams) => string;

// Navigation function type
export type NavigateFunction = <T extends RoutePath>(
  route: T,
  ...args: HasParams<T> extends true
    ? [params: RouteParams<T>, options?: { query?: QueryParams; replace?: boolean; state?: unknown }]
    : [options?: { query?: QueryParams; replace?: boolean; state?: unknown }]
) => void;

// URL builder functions
export const buildUrl = <T extends RoutePath>(route: T) => {
  return ((...args: any[]) => {
    let url = route as string;
    const [paramsOrQuery, queryOrOptions] = args;

    // If route has parameters, replace them
    if (paramsOrQuery && typeof paramsOrQuery === 'object' && !Array.isArray(paramsOrQuery)) {
      // Check if first argument contains route parameters
      const hasRouteParams = Object.keys(paramsOrQuery).some(key => url.includes(`:${key}`));

      if (hasRouteParams) {
        // Replace route parameters
        Object.entries(paramsOrQuery).forEach(([key, value]) => {
          if (url.includes(`:${key}`)) {
            url = url.replace(`:${key}`, String(value));
          }
        });

        // Add query parameters if provided in second argument
        if (queryOrOptions?.query) {
          const searchParams = new URLSearchParams();
          Object.entries(queryOrOptions.query).forEach(([key, value]) => {
            if (value !== undefined) {
              searchParams.append(key, String(value));
            }
          });
          if (searchParams.toString()) {
            url += `?${searchParams.toString()}`;
          }
        }
      } else {
        // First argument is query parameters
        const searchParams = new URLSearchParams();
        Object.entries(paramsOrQuery).forEach(([key, value]) => {
          if (value !== undefined) {
            searchParams.append(key, String(value));
          }
        });
        if (searchParams.toString()) {
          url += `?${searchParams.toString()}`;
        }
      }
    }

    return url;
  }) as BuildUrl<T>;
};

// Pre-built URL builders for common routes
export const routes = {
  home: buildUrl('/'),
  login: buildUrl('/login'),
  register: buildUrl('/register'),
  dashboard: buildUrl('/dashboard'),
  profile: buildUrl('/profile'),
  settings: buildUrl('/settings'),

  // Class routes
  class: buildUrl('/dashboard/classes/:classId'),
  classStudents: buildUrl('/dashboard/classes/:classId/students'),
  classLessons: buildUrl('/dashboard/classes/:classId/lessons'),
  classAssessments: buildUrl('/dashboard/classes/:classId/assessments'),

  // Lesson routes
  lesson: buildUrl('/dashboard/lessons/:lessonId'),
  editLesson: buildUrl('/dashboard/lessons/:lessonId/edit'),

  // Assessment routes
  assessment: buildUrl('/dashboard/assessments/:assessmentId'),
  takeAssessment: buildUrl('/dashboard/assessments/:assessmentId/take'),
  assessmentResults: buildUrl('/dashboard/assessments/:assessmentId/results'),

  // User routes
  user: buildUrl('/dashboard/users/:userId'),
  editUser: buildUrl('/dashboard/users/:userId/edit'),

  // Message routes
  message: buildUrl('/dashboard/messages/:messageId'),

  // Roblox routes
  robloxWorld: buildUrl('/dashboard/roblox/worlds/:worldId'),
  joinRobloxWorld: buildUrl('/dashboard/roblox/worlds/:worldId/join'),
} as const;

// Type-safe link component props
export type LinkProps<T extends RoutePath> = {
  to: T;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  replace?: boolean;
  state?: unknown;
} & (HasParams<T> extends true
  ? { params: RouteParams<T>; query?: QueryParams }
  : { params?: never; query?: QueryParams });

// Route guard types
export type RouteGuard = {
  path: RoutePath | RoutePath[];
  guard: (user: { role: string; permissions: string[] }) => boolean;
  redirectTo?: RoutePath;
  message?: string;
};

// Route metadata
export type RouteMetadata = {
  title: string;
  description?: string;
  requiresAuth: boolean;
  roles?: string[];
  permissions?: string[];
  breadcrumbs?: { label: string; path?: RoutePath }[];
  sidebarSection?: string;
  hideNavbar?: boolean;
  hideSidebar?: boolean;
  fullscreen?: boolean;
};

// Complete route configuration
export type RouteConfig<T extends RoutePath = RoutePath> = {
  path: T;
  component: React.ComponentType<any>;
  metadata: RouteMetadata;
  guards?: RouteGuard[];
  children?: RouteConfig[];
};

// Dynamic route imports
export type RouteImport = () => Promise<{ default: React.ComponentType<any> }>;

// Lazy route configuration
export type LazyRouteConfig<T extends RoutePath = RoutePath> = Omit<RouteConfig<T>, 'component'> & {
  import: RouteImport;
  fallback?: React.ComponentType;
};

// Route matcher
export type RouteMatcher = {
  pattern: string;
  keys: string[];
  regexp: RegExp;
};

// Navigation history entry
export type HistoryEntry = {
  pathname: string;
  search: string;
  hash: string;
  state: unknown;
  key: string;
  timestamp: number;
};

// Navigation context
export type NavigationContext = {
  location: HistoryEntry;
  history: HistoryEntry[];
  navigate: NavigateFunction;
  canGoBack: boolean;
  canGoForward: boolean;
  goBack: () => void;
  goForward: () => void;
};

// URL parsing utilities
export type ParsedUrl = {
  pathname: string;
  params: Record<string, string>;
  query: QueryParams;
  hash: string;
};

// Route validation
export type RouteValidation = {
  isValid: boolean;
  errors: string[];
  warnings: string[];
};

// Helper functions for type-safe routing
export const parseUrl = (url: string, pattern: string): ParsedUrl => {
  const [pathname, search, hash] = url.split(/[?#]/);

  // Extract parameters from pathname
  const params: Record<string, string> = {};
  const patternSegments = pattern.split('/');
  const pathSegments = pathname.split('/');

  patternSegments.forEach((segment, index) => {
    if (segment.startsWith(':')) {
      const paramName = segment.slice(1);
      params[paramName] = pathSegments[index] || '';
    }
  });

  // Parse query parameters
  const query: QueryParams = {};
  if (search) {
    const searchParams = new URLSearchParams(search);
    searchParams.forEach((value, key) => {
      // Try to parse as number
      const numValue = Number(value);
      if (!isNaN(numValue) && isFinite(numValue)) {
        (query as any)[key] = numValue;
      } else if (value === 'true') {
        (query as any)[key] = true;
      } else if (value === 'false') {
        (query as any)[key] = false;
      } else {
        (query as any)[key] = value;
      }
    });
  }

  return {
    pathname,
    params,
    query,
    hash: hash || '',
  };
};

export const validateRoute = (path: string): RouteValidation => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check for valid route format
  if (!path.startsWith('/')) {
    errors.push('Route must start with "/"');
  }

  // Check for consecutive slashes
  if (path.includes('//')) {
    errors.push('Route cannot contain consecutive slashes');
  }

  // Check for trailing slash (except root)
  if (path !== '/' && path.endsWith('/')) {
    warnings.push('Route should not end with "/" (except root route)');
  }

  // Check parameter format
  const paramPattern = /:([a-zA-Z_$][a-zA-Z0-9_$]*)/g;
  const matches = [...path.matchAll(paramPattern)];
  const paramNames = matches.map(match => match[1]);
  const uniqueParams = new Set(paramNames);

  if (paramNames.length !== uniqueParams.size) {
    errors.push('Route cannot have duplicate parameter names');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
};

// Generate route matcher
export const createRouteMatcher = (pattern: string): RouteMatcher => {
  const keys: string[] = [];
  const regexp = new RegExp(
    '^' + pattern.replace(/:([a-zA-Z_$][a-zA-Z0-9_$]*)/g, (_, key) => {
      keys.push(key);
      return '([^/]+)';
    }) + '$'
  );

  return { pattern, keys, regexp };
};

// Check if URL matches pattern
export const matchRoute = (url: string, pattern: string): { matches: boolean; params: Record<string, string> } => {
  const matcher = createRouteMatcher(pattern);
  const match = url.match(matcher.regexp);

  if (!match) {
    return { matches: false, params: {} };
  }

  const params: Record<string, string> = {};
  matcher.keys.forEach((key, index) => {
    params[key] = match[index + 1];
  });

  return { matches: true, params };
};
