// Legacy exports for backward compatibility
export { type UserRole, type RolePermissions, ROLE_PERMISSIONS } from './roles';

// API types - explicitly export to avoid conflicts
export {
  type User,
  type UserCreate,
  type UserUpdate,
  type AuthResponse,
  type Lesson,
  type ClassSummary,
  type ClassDetails,
  type Student,
  type Badge,
  type XPTransaction,
  type LeaderboardEntry,
  type Assessment,
  type Question,
  type AssessmentSubmission,
  type ProgressPoint,
  type StudentProgress,
  type SubjectProgress,
  type Notification,
  type Message,
  type DashboardMetrics,
  // Note: Achievement and ApiError are not exported from api.ts, they may be internal
  type Mission,
  type MissionProgress,
  type MissionRequirement,
  type Reward,
  type RewardRedemption,
  type Event,
  type RobloxWorld,
  type ApiResponse,
  type ComplianceCheck,
  type ComplianceStatus as ApiComplianceStatus,
} from './api';

// Re-export specific items from other modules to avoid conflicts
export * from './branded';
export * from './discriminated-unions';
export * from './utility-types';
export * from './routes';
export * from './events';
export * from './websocket';
export * from './pusher';

// Schema exports - only export schemas, not types (to avoid conflicts with api.ts)
export {
  IdSchema,
  EmailSchema,
  UrlSchema,
  DateStringSchema,
  NonNegativeNumberSchema,
  PositiveNumberSchema,
  ProgressPercentageSchema,
  UserRoleSchema,
  UserStatusSchema,
  SubjectSchema,
  LessonStatusSchema,
  BadgeCategorySchema,
  BadgeRaritySchema,
  AssessmentTypeSchema,
  AssessmentStatusSchema,
  QuestionTypeSchema,
  XPSourceSchema,
  NotificationTypeSchema,
  ComplianceStatusSchema,
  MissionTypeSchema,
} from './schemas';

// Enhanced Redux State Types with strict typing
export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  language: string;
  notifications: NotificationItem[];
}

export interface UserState {
  userId?: string;
  email?: string;
  displayName?: string;
  avatarUrl?: string;
  role: import('./roles').UserRole;
  isAuthenticated: boolean;
  token?: string;
  refreshToken?: string;
}

export interface DashboardState {
  loading: boolean;
  error: string | null;
  metrics: import('./api').DashboardMetrics | null;
  recentActivity: import('./api').Activity[];
  upcomingEvents: import('./api').Event[];
}

export interface GamificationState {
  xp: number;
  level: number;
  nextLevelXP: number;
  badges: import('./api').Badge[];
  leaderboard: import('./api').LeaderboardEntry[];
  recentXPTransactions: import('./api').XPTransaction[];
}

export interface NotificationItem {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  message: string;
  timestamp: number;
  autoHide?: boolean;
}

// Type-safe configuration
export interface TypeSafetyConfig {
  strictMode: boolean;
  runtimeValidation: boolean;
  brandedTypes: boolean;
  exhaustivenessChecking: boolean;
  noImplicitAny: boolean;
  exactOptionalPropertyTypes: boolean;
}

// Global type safety configuration
export const TYPE_SAFETY_CONFIG: TypeSafetyConfig = {
  strictMode: true,
  runtimeValidation: true,
  brandedTypes: true,
  exhaustivenessChecking: true,
  noImplicitAny: true,
  exactOptionalPropertyTypes: true,
} as const;

// Type assertion helpers
export const assertNever = (value: never): never => {
  throw new Error(`Unexpected value: ${JSON.stringify(value)}`);
};

export const isNotNullish = <T>(value: T | null | undefined): value is T => {
  return value !== null && value !== undefined;
};

// Runtime type checking helpers
export const ensureType = <T>(value: unknown, validator: (val: unknown) => val is T): T => {
  if (!validator(value)) {
    throw new Error('Type validation failed');
  }
  return value;
};

// Exhaustive switch helper
export const exhaustiveSwitch = (value: never): never => {
  throw new Error(`Unhandled case: ${JSON.stringify(value)}`);
};

// Re-export commonly used types for convenience
export type {
  // Schema types (from Zod) - includes runtime validation
  // Note: User, Badge, Student, Assessment, Lesson, ClassSummary, ClassDetails, StudentProgress
  // are already exported from './api' above to avoid conflicts
  DashboardOverview,
} from './schemas';

export type {
  LoadingState,
  AuthState,
  DataState,
  FormState,
  WebSocketState,
  UserSessionState,
  ModalState,
  NotificationState,
} from './discriminated-unions';

export type {
  RequiredBy,
  OptionalBy,
  DeepPartial,
  DeepRequired,
  Nullable,
  NonNullable,
  WithChildren,
  WithClassName,
  WithStyle,
  // Note: ApiResponse is already exported from './api' above
  PaginatedResponse,
  ErrorResponse,
  SuccessResponse,
} from './utility-types';

export type {
  RoutePath,
  RouteParams,
  NavigateFunction,
  LinkProps,
} from './routes';

export type {
  AppEvent,
  EventHandler,
  AsyncEventHandler,
  FormEvents,
  InputEvents,
  ButtonEvents,
  ModalEvents,
} from './events';

export type {
  UserId,
  ClassId,
  LessonId,
  AssessmentId,
  XPPoints,
  Level,
  ProgressPercentage,
  Timestamp,
  Email,
  Username,
  DisplayName,
} from './branded';

// Type guards for common patterns
export const isString = (value: unknown): value is string =>
  typeof value === 'string';

export const isNumber = (value: unknown): value is number =>
  typeof value === 'number' && !isNaN(value);

export const isBoolean = (value: unknown): value is boolean =>
  typeof value === 'boolean';

export const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

export const isArray = <T = unknown>(value: unknown): value is T[] =>
  Array.isArray(value);

export const isFunction = (value: unknown): value is Function =>
  typeof value === 'function';

export const isPromise = <T = unknown>(value: unknown): value is Promise<T> =>
  value instanceof Promise || (isObject(value) && isFunction((value as any).then));

// Performance type checking (for development)
export const withTypeChecking = <T extends (...args: any[]) => any>(
  fn: T,
  typeName: string
): T => {
  if (process.env.NODE_ENV !== 'development') {
    return fn;
  }

  return ((...args: Parameters<T>): ReturnType<T> => {
    console.time(`Type check: ${typeName}`);
    const result = fn(...args);
    console.timeEnd(`Type check: ${typeName}`);
    return result;
  }) as T;
};

// Type-safe environment for runtime validation
export const TYPE_SAFE_ENV = {
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  isTest: process.env.NODE_ENV === 'test',
  enableRuntimeValidation: process.env.NODE_ENV !== 'production',
  enableTypeChecking: process.env.NODE_ENV === 'development',
} as const;

// Export validation helpers from schemas
export { validateApiResponse } from './schemas';

// Export utility functions from other modules
export {
  // Branded type constructors
  createUserId,
  createClassId,
  createLessonId,
  createXPPoints,
  createLevel,
  createProgressPercentage,
  createEmail,
  createUsername,
  createDisplayName,

  // Type guards for branded types
  isUserId,
  isClassId,
  isLessonId,
  isXPPoints,
  isLevel,
  isProgressPercentage,
  isEmail,
  isUsername,
  isDisplayName,
} from './branded';

export {
  // State creators
  createLoadingState,
  createAuthState,
  createDataState,
  createFormState,

  // Type guards for discriminated unions
  isLoadingState,
  isAuthState,
  isDataState,
  isFormState,
  isWebSocketState,
  isUserSessionState,
} from './discriminated-unions';

export {
  // Route utilities
  buildUrl,
  routes,
  parseUrl,
  validateRoute,
  createRouteMatcher,
  matchRoute,
} from './routes';

export {
  // Event utilities
  createEvent,
  isEventType,
  createEventHandler,
  createAsyncEventHandler,
  createKeyboardShortcut,
  throttle,
  debounce,
} from './events';

export {
  // Utility functions
  typedKeys,
  typedEntries,
  isNotNull,
  isDefined,
  isNonEmptyArray,
  isNonEmptyString,
  isPositiveNumber,
  isNonNegativeNumber,
  hasProperty,
} from './utility-types';

// Type-safe global utilities for the entire application
declare global {
  interface Window {
    __TYPE_SAFE_MODE__?: boolean;
    __RUNTIME_VALIDATION__?: boolean;
  }
}

// Enable type-safe mode in development
if (typeof window !== 'undefined' && TYPE_SAFE_ENV.isDevelopment) {
  window.__TYPE_SAFE_MODE__ = true;
  window.__RUNTIME_VALIDATION__ = TYPE_SAFETY_CONFIG.runtimeValidation;
}