/**
 * Discriminated Unions for Type-Safe State Management
 *
 * These discriminated unions ensure that state transitions are type-safe
 * and help prevent impossible states in the application.
 */

import type {
  UserId,
  ClassId,
  LessonId,
  AssessmentId,
  NotificationId,
  XPPoints,
  Level,
  ProgressPercentage,
  Timestamp,
} from './branded';

// Loading States
export type LoadingState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'succeeded'; lastUpdated: Timestamp }
  | { status: 'failed'; error: string; lastAttempt: Timestamp };

// Authentication States
export type AuthState =
  | { status: 'unauthenticated' }
  | { status: 'authenticating' }
  | { status: 'authenticated'; userId: UserId; token: string; expiresAt: Timestamp }
  | { status: 'expired'; userId: UserId; lastToken: string }
  | { status: 'error'; error: string };

// Data Fetch States
export type DataState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'succeeded'; data: T; lastFetched: Timestamp }
  | { status: 'failed'; error: string; lastAttempt: Timestamp }
  | { status: 'stale'; data: T; lastFetched: Timestamp };

// Form States
export type FormState<T> =
  | { status: 'idle'; values: Partial<T> }
  | { status: 'validating'; values: T }
  | { status: 'submitting'; values: T }
  | { status: 'success'; submittedValues: T; timestamp: Timestamp }
  | { status: 'error'; values: T; error: string; fieldErrors?: Record<keyof T, string> };

// WebSocket Connection States
export type WebSocketState =
  | { status: 'disconnected' }
  | { status: 'connecting' }
  | { status: 'connected'; connectedAt: Timestamp }
  | { status: 'reconnecting'; lastConnected: Timestamp; attempt: number }
  | { status: 'error'; error: string; lastAttempt: Timestamp };

// User Session States
export type UserSessionState =
  | { type: 'guest' }
  | { type: 'student'; userId: UserId; classIds: ClassId[]; xp: XPPoints; level: Level }
  | { type: 'teacher'; userId: UserId; classIds: ClassId[]; schoolId?: string }
  | { type: 'parent'; userId: UserId; childIds: UserId[] }
  | { type: 'admin'; userId: UserId; permissions: string[] };

// Modal States
export type ModalState =
  | { isOpen: false }
  | { isOpen: true; type: 'create-class'; initialData?: Partial<{ name: string; grade: number }> }
  | { isOpen: true; type: 'create-lesson'; classId?: ClassId }
  | { isOpen: true; type: 'create-assessment'; lessonId?: LessonId }
  | { isOpen: true; type: 'edit-user'; userId: UserId }
  | { isOpen: true; type: 'confirm-delete'; itemType: string; itemId: string; onConfirm: () => void }
  | { isOpen: true; type: 'view-details'; itemType: string; itemId: string };

// Notification States
export type NotificationState =
  | { type: 'info'; id: NotificationId; message: string; autoHide: true; duration: number }
  | { type: 'success'; id: NotificationId; message: string; autoHide: boolean; duration?: number }
  | { type: 'warning'; id: NotificationId; message: string; autoHide: false; actions?: NotificationAction[] }
  | { type: 'error'; id: NotificationId; message: string; autoHide: false; actions?: NotificationAction[] };

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

// Assessment States
export type AssessmentSessionState =
  | { status: 'not-started'; assessmentId: AssessmentId }
  | { status: 'in-progress'; assessmentId: AssessmentId; currentQuestion: number; answers: unknown[]; startedAt: Timestamp }
  | { status: 'paused'; assessmentId: AssessmentId; currentQuestion: number; answers: unknown[]; pausedAt: Timestamp }
  | { status: 'submitted'; assessmentId: AssessmentId; submittedAt: Timestamp; awaitingGrade: boolean }
  | { status: 'completed'; assessmentId: AssessmentId; score: number; feedback?: string };

// Content Generation States
export type ContentGenerationState =
  | { status: 'idle' }
  | { status: 'generating'; progress: ProgressPercentage; currentStep: string }
  | { status: 'review'; content: unknown; requiresApproval: boolean }
  | { status: 'completed'; contentId: string; createdAt: Timestamp }
  | { status: 'failed'; error: string; retryable: boolean };

// Roblox World States
export type RobloxWorldState =
  | { status: 'not-connected' }
  | { status: 'connecting'; worldId: string }
  | { status: 'connected'; worldId: string; playerId: string; connectedAt: Timestamp }
  | { status: 'in-game'; worldId: string; playerId: string; gameData: unknown }
  | { status: 'disconnected'; lastWorldId: string; reason: string };

// Progress Tracking States
export type ProgressState =
  | { type: 'not-started'; lessonId: LessonId }
  | { type: 'in-progress'; lessonId: LessonId; progress: ProgressPercentage; lastActivity: Timestamp }
  | { type: 'completed'; lessonId: LessonId; completedAt: Timestamp; score?: number }
  | { type: 'mastered'; lessonId: LessonId; masteredAt: Timestamp; masteryScore: number };

// Search States
export type SearchState<T> =
  | { status: 'idle'; query: '' }
  | { status: 'searching'; query: string }
  | { status: 'results'; query: string; results: T[]; totalCount: number; searchedAt: Timestamp }
  | { status: 'no-results'; query: string; searchedAt: Timestamp }
  | { status: 'error'; query: string; error: string };

// File Upload States
export type FileUploadState =
  | { status: 'idle' }
  | { status: 'selecting' }
  | { status: 'uploading'; progress: ProgressPercentage; filename: string }
  | { status: 'processing'; filename: string }
  | { status: 'completed'; url: string; filename: string }
  | { status: 'failed'; error: string; filename: string };

// Chat/Message States
export type ChatState =
  | { status: 'idle' }
  | { status: 'typing'; recipientId: UserId }
  | { status: 'sending'; message: string; recipientId: UserId }
  | { status: 'sent'; messageId: string; sentAt: Timestamp }
  | { status: 'failed'; message: string; error: string };

// Gamification State
export type GamificationEvent =
  | { type: 'xp-gained'; amount: XPPoints; source: string; timestamp: Timestamp }
  | { type: 'level-up'; newLevel: Level; xpEarned: XPPoints; timestamp: Timestamp }
  | { type: 'badge-earned'; badgeId: string; badgeName: string; timestamp: Timestamp }
  | { type: 'streak-milestone'; days: number; bonusXP: XPPoints; timestamp: Timestamp }
  | { type: 'achievement-unlocked'; achievementId: string; title: string; timestamp: Timestamp };

// Dashboard Tab States
export type DashboardTab =
  | { active: 'overview'; filters?: { timeRange: 'day' | 'week' | 'month' | 'year' } }
  | { active: 'classes'; filters?: { status: 'active' | 'archived' | 'all' } }
  | { active: 'lessons'; filters?: { subject: string; status: string } }
  | { active: 'students'; filters?: { classId: ClassId; sortBy: 'name' | 'xp' | 'progress' } }
  | { active: 'reports'; filters?: { type: 'progress' | 'engagement' | 'compliance' } }
  | { active: 'settings'; section?: 'profile' | 'notifications' | 'privacy' | 'integrations' };

// Permission States
export type PermissionState =
  | { status: 'unknown' }
  | { status: 'granted'; grantedAt: Timestamp }
  | { status: 'denied'; reason: string }
  | { status: 'requesting' }
  | { status: 'expired'; expiredAt: Timestamp };

// Sync States for offline-first functionality
export type SyncState<T> =
  | { status: 'synced'; data: T; lastSync: Timestamp }
  | { status: 'pending'; data: T; changes: Partial<T>; lastChange: Timestamp }
  | { status: 'syncing'; data: T; changes: Partial<T> }
  | { status: 'conflict'; local: T; remote: T; conflictedAt: Timestamp }
  | { status: 'error'; data: T; error: string; lastAttempt: Timestamp };

// Type guards for discriminated unions
export const isLoadingState = (state: LoadingState, status: LoadingState['status']): state is Extract<LoadingState, { status: typeof status }> =>
  state.status === status;

export const isAuthState = (state: AuthState, status: AuthState['status']): state is Extract<AuthState, { status: typeof status }> =>
  state.status === status;

export const isDataState = <T>(state: DataState<T>, status: DataState<T>['status']): state is Extract<DataState<T>, { status: typeof status }> =>
  state.status === status;

export const isFormState = <T>(state: FormState<T>, status: FormState<T>['status']): state is Extract<FormState<T>, { status: typeof status }> =>
  state.status === status;

export const isWebSocketState = (state: WebSocketState, status: WebSocketState['status']): state is Extract<WebSocketState, { status: typeof status }> =>
  state.status === status;

export const isUserSessionState = (state: UserSessionState, type: UserSessionState['type']): state is Extract<UserSessionState, { type: typeof type }> =>
  state.type === type;

export const isNotificationState = (state: NotificationState, type: NotificationState['type']): state is Extract<NotificationState, { type: typeof type }> =>
  state.type === type;

export const isAssessmentSessionState = (state: AssessmentSessionState, status: AssessmentSessionState['status']): state is Extract<AssessmentSessionState, { status: typeof status }> =>
  state.status === status;

export const isContentGenerationState = (state: ContentGenerationState, status: ContentGenerationState['status']): state is Extract<ContentGenerationState, { status: typeof status }> =>
  state.status === status;

export const isRobloxWorldState = (state: RobloxWorldState, status: RobloxWorldState['status']): state is Extract<RobloxWorldState, { status: typeof status }> =>
  state.status === status;

export const isProgressState = (state: ProgressState, type: ProgressState['type']): state is Extract<ProgressState, { type: typeof type }> =>
  state.type === type;

export const isSearchState = <T>(state: SearchState<T>, status: SearchState<T>['status']): state is Extract<SearchState<T>, { status: typeof status }> =>
  state.status === status;

export const isFileUploadState = (state: FileUploadState, status: FileUploadState['status']): state is Extract<FileUploadState, { status: typeof status }> =>
  state.status === status;

export const isChatState = (state: ChatState, status: ChatState['status']): state is Extract<ChatState, { status: typeof status }> =>
  state.status === status;

export const isGamificationEvent = (event: GamificationEvent, type: GamificationEvent['type']): event is Extract<GamificationEvent, { type: typeof type }> =>
  event.type === type;

export const isDashboardTab = (tab: DashboardTab, active: DashboardTab['active']): tab is Extract<DashboardTab, { active: typeof active }> =>
  tab.active === active;

export const isPermissionState = (state: PermissionState, status: PermissionState['status']): state is Extract<PermissionState, { status: typeof status }> =>
  state.status === status;

export const isSyncState = <T>(state: SyncState<T>, status: SyncState<T>['status']): state is Extract<SyncState<T>, { status: typeof status }> =>
  state.status === status;

// Helper functions for state transitions
export const createLoadingState = {
  idle: (): LoadingState => ({ status: 'idle' }),
  loading: (): LoadingState => ({ status: 'loading' }),
  succeeded: (lastUpdated: Timestamp = new Date().toISOString() as Timestamp): LoadingState => ({ status: 'succeeded', lastUpdated }),
  failed: (error: string, lastAttempt: Timestamp = new Date().toISOString() as Timestamp): LoadingState => ({ status: 'failed', error, lastAttempt }),
};

export const createAuthState = {
  unauthenticated: (): AuthState => ({ status: 'unauthenticated' }),
  authenticating: (): AuthState => ({ status: 'authenticating' }),
  authenticated: (userId: UserId, token: string, expiresAt: Timestamp): AuthState => ({ status: 'authenticated', userId, token, expiresAt }),
  expired: (userId: UserId, lastToken: string): AuthState => ({ status: 'expired', userId, lastToken }),
  error: (error: string): AuthState => ({ status: 'error', error }),
};

export const createDataState = {
  idle: <T>(): DataState<T> => ({ status: 'idle' }),
  loading: <T>(): DataState<T> => ({ status: 'loading' }),
  succeeded: <T>(data: T, lastFetched: Timestamp = new Date().toISOString() as Timestamp): DataState<T> => ({ status: 'succeeded', data, lastFetched }),
  failed: <T>(error: string, lastAttempt: Timestamp = new Date().toISOString() as Timestamp): DataState<T> => ({ status: 'failed', error, lastAttempt }),
  stale: <T>(data: T, lastFetched: Timestamp): DataState<T> => ({ status: 'stale', data, lastFetched }),
};

export const createFormState = {
  idle: <T>(values: Partial<T> = {}): FormState<T> => ({ status: 'idle', values }),
  validating: <T>(values: T): FormState<T> => ({ status: 'validating', values }),
  submitting: <T>(values: T): FormState<T> => ({ status: 'submitting', values }),
  success: <T>(submittedValues: T, timestamp: Timestamp = new Date().toISOString() as Timestamp): FormState<T> => ({ status: 'success', submittedValues, timestamp }),
  error: <T>(values: T, error: string, fieldErrors?: Record<keyof T, string>): FormState<T> => ({ status: 'error', values, error, fieldErrors }),
};