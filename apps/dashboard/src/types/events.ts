/**
 * Type-Safe Event Handlers and Custom Events
 *
 * These types provide compile-time safety for event handling throughout the application,
 * ensuring proper event types and preventing common event handling errors.
 */

import type {
  UserId,
  ClassId,
  LessonId,
  AssessmentId,
  MessageId,
  XPPoints,
  Level,
  ProgressPercentage,
  Timestamp,
} from './branded';

// Base event interface
export interface BaseEvent {
  type: string;
  timestamp: Timestamp;
  source: 'user' | 'system' | 'api' | 'websocket';
  metadata?: Record<string, unknown>;
}

// DOM Event types with proper typing
export type InputChangeEvent = React.ChangeEvent<HTMLInputElement>;
export type TextAreaChangeEvent = React.ChangeEvent<HTMLTextAreaElement>;
export type SelectChangeEvent = React.ChangeEvent<HTMLSelectElement>;
export type FormSubmitEvent = React.FormEvent<HTMLFormElement>;
export type ButtonClickEvent = React.MouseEvent<HTMLButtonElement>;
export type DivClickEvent = React.MouseEvent<HTMLDivElement>;
export type KeyboardEvent = React.KeyboardEvent<HTMLElement>;
export type FocusEvent = React.FocusEvent<HTMLElement>;
export type BlurEvent = React.FocusEvent<HTMLElement>;

// Custom Application Events
export interface UserEvents {
  'user:login': BaseEvent & {
    type: 'user:login';
    payload: {
      userId: UserId;
      role: string;
      timestamp: Timestamp;
    };
  };

  'user:logout': BaseEvent & {
    type: 'user:logout';
    payload: {
      userId: UserId;
      sessionDuration: number;
      timestamp: Timestamp;
    };
  };

  'user:profile-updated': BaseEvent & {
    type: 'user:profile-updated';
    payload: {
      userId: UserId;
      changes: Record<string, unknown>;
      timestamp: Timestamp;
    };
  };

  'user:password-changed': BaseEvent & {
    type: 'user:password-changed';
    payload: {
      userId: UserId;
      timestamp: Timestamp;
    };
  };
}

export interface ClassEvents {
  'class:created': BaseEvent & {
    type: 'class:created';
    payload: {
      classId: ClassId;
      teacherId: UserId;
      name: string;
      grade: number;
      timestamp: Timestamp;
    };
  };

  'class:updated': BaseEvent & {
    type: 'class:updated';
    payload: {
      classId: ClassId;
      changes: Record<string, unknown>;
      updatedBy: UserId;
      timestamp: Timestamp;
    };
  };

  'class:student-added': BaseEvent & {
    type: 'class:student-added';
    payload: {
      classId: ClassId;
      studentId: UserId;
      addedBy: UserId;
      timestamp: Timestamp;
    };
  };

  'class:student-removed': BaseEvent & {
    type: 'class:student-removed';
    payload: {
      classId: ClassId;
      studentId: UserId;
      removedBy: UserId;
      reason?: string;
      timestamp: Timestamp;
    };
  };
}

export interface LessonEvents {
  'lesson:created': BaseEvent & {
    type: 'lesson:created';
    payload: {
      lessonId: LessonId;
      title: string;
      subject: string;
      teacherId: UserId;
      classIds: ClassId[];
      timestamp: Timestamp;
    };
  };

  'lesson:started': BaseEvent & {
    type: 'lesson:started';
    payload: {
      lessonId: LessonId;
      studentId: UserId;
      classId: ClassId;
      timestamp: Timestamp;
    };
  };

  'lesson:completed': BaseEvent & {
    type: 'lesson:completed';
    payload: {
      lessonId: LessonId;
      studentId: UserId;
      classId: ClassId;
      completionTime: number;
      score?: number;
      timestamp: Timestamp;
    };
  };

  'lesson:progress-updated': BaseEvent & {
    type: 'lesson:progress-updated';
    payload: {
      lessonId: LessonId;
      studentId: UserId;
      progress: ProgressPercentage;
      timestamp: Timestamp;
    };
  };
}

export interface AssessmentEvents {
  'assessment:created': BaseEvent & {
    type: 'assessment:created';
    payload: {
      assessmentId: AssessmentId;
      title: string;
      type: 'quiz' | 'test' | 'assignment' | 'project';
      createdBy: UserId;
      classId: ClassId;
      timestamp: Timestamp;
    };
  };

  'assessment:started': BaseEvent & {
    type: 'assessment:started';
    payload: {
      assessmentId: AssessmentId;
      studentId: UserId;
      attempt: number;
      timestamp: Timestamp;
    };
  };

  'assessment:submitted': BaseEvent & {
    type: 'assessment:submitted';
    payload: {
      assessmentId: AssessmentId;
      studentId: UserId;
      submissionId: string;
      answers: unknown[];
      timeSpent: number;
      timestamp: Timestamp;
    };
  };

  'assessment:graded': BaseEvent & {
    type: 'assessment:graded';
    payload: {
      assessmentId: AssessmentId;
      studentId: UserId;
      submissionId: string;
      score: number;
      maxScore: number;
      gradedBy: UserId;
      feedback?: string;
      timestamp: Timestamp;
    };
  };
}

export interface GamificationEvents {
  'xp:earned': BaseEvent & {
    type: 'xp:earned';
    payload: {
      studentId: UserId;
      amount: XPPoints;
      source: 'lesson' | 'assessment' | 'achievement' | 'bonus';
      description: string;
      timestamp: Timestamp;
    };
  };

  'level:up': BaseEvent & {
    type: 'level:up';
    payload: {
      studentId: UserId;
      newLevel: Level;
      xpEarned: XPPoints;
      rewards?: string[];
      timestamp: Timestamp;
    };
  };

  'badge:earned': BaseEvent & {
    type: 'badge:earned';
    payload: {
      studentId: UserId;
      badgeId: string;
      badgeName: string;
      category: 'achievement' | 'milestone' | 'special' | 'seasonal';
      rarity: 'common' | 'rare' | 'epic' | 'legendary';
      timestamp: Timestamp;
    };
  };

  'streak:updated': BaseEvent & {
    type: 'streak:updated';
    payload: {
      studentId: UserId;
      streakDays: number;
      streakType: 'daily_login' | 'lesson_completion' | 'assessment_submission';
      bonusXP?: XPPoints;
      timestamp: Timestamp;
    };
  };
}

export interface MessageEvents {
  'message:sent': BaseEvent & {
    type: 'message:sent';
    payload: {
      messageId: MessageId;
      fromUserId: UserId;
      toUserId: UserId;
      subject: string;
      hasAttachments: boolean;
      timestamp: Timestamp;
    };
  };

  'message:received': BaseEvent & {
    type: 'message:received';
    payload: {
      messageId: MessageId;
      fromUserId: UserId;
      toUserId: UserId;
      subject: string;
      isUrgent: boolean;
      timestamp: Timestamp;
    };
  };

  'message:read': BaseEvent & {
    type: 'message:read';
    payload: {
      messageId: MessageId;
      userId: UserId;
      timestamp: Timestamp;
    };
  };
}

export interface SystemEvents {
  'system:maintenance-start': BaseEvent & {
    type: 'system:maintenance-start';
    payload: {
      estimatedDuration: number;
      reason: string;
      timestamp: Timestamp;
    };
  };

  'system:maintenance-end': BaseEvent & {
    type: 'system:maintenance-end';
    payload: {
      actualDuration: number;
      timestamp: Timestamp;
    };
  };

  'system:error': BaseEvent & {
    type: 'system:error';
    payload: {
      errorCode: string;
      errorMessage: string;
      userId?: UserId;
      stackTrace?: string;
      timestamp: Timestamp;
    };
  };

  'system:performance-warning': BaseEvent & {
    type: 'system:performance-warning';
    payload: {
      metric: string;
      value: number;
      threshold: number;
      timestamp: Timestamp;
    };
  };
}

export interface RobloxEvents {
  'roblox:world-joined': BaseEvent & {
    type: 'roblox:world-joined';
    payload: {
      worldId: string;
      studentId: UserId;
      placeId: string;
      sessionId: string;
      timestamp: Timestamp;
    };
  };

  'roblox:world-left': BaseEvent & {
    type: 'roblox:world-left';
    payload: {
      worldId: string;
      studentId: UserId;
      sessionId: string;
      sessionDuration: number;
      reason: 'user_quit' | 'kicked' | 'error' | 'maintenance';
      timestamp: Timestamp;
    };
  };

  'roblox:achievement-unlocked': BaseEvent & {
    type: 'roblox:achievement-unlocked';
    payload: {
      worldId: string;
      studentId: UserId;
      achievementId: string;
      achievementName: string;
      xpReward: XPPoints;
      timestamp: Timestamp;
    };
  };
}

// Union of all event types
export type AppEvent =
  | UserEvents[keyof UserEvents]
  | ClassEvents[keyof ClassEvents]
  | LessonEvents[keyof LessonEvents]
  | AssessmentEvents[keyof AssessmentEvents]
  | GamificationEvents[keyof GamificationEvents]
  | MessageEvents[keyof MessageEvents]
  | SystemEvents[keyof SystemEvents]
  | RobloxEvents[keyof RobloxEvents];

// Event handler types
export type EventHandler<T extends AppEvent> = (event: T) => void;
export type AsyncEventHandler<T extends AppEvent> = (event: T) => Promise<void>;

// Event listener configuration
export interface EventListener<T extends AppEvent = AppEvent> {
  type: T['type'];
  handler: EventHandler<T> | AsyncEventHandler<T>;
  options?: {
    once?: boolean;
    capture?: boolean;
    passive?: boolean;
    signal?: AbortSignal;
  };
}

// Event emitter interface
export interface EventEmitter {
  emit<T extends AppEvent>(event: T): void;
  on<T extends AppEvent>(type: T['type'], handler: EventHandler<T>): () => void;
  off<T extends AppEvent>(type: T['type'], handler: EventHandler<T>): void;
  once<T extends AppEvent>(type: T['type'], handler: EventHandler<T>): () => void;
  removeAllListeners(type?: string): void;
  listenerCount(type: string): number;
}

// Form event types
export interface FormEvents {
  onSubmit: (event: FormSubmitEvent) => void;
  onReset?: (event: React.FormEvent<HTMLFormElement>) => void;
  onChange?: (field: string, value: unknown) => void;
  onValidate?: (field: string, value: unknown) => string | undefined;
  onError?: (errors: Record<string, string>) => void;
}

// Input event types
export interface InputEvents {
  onChange: (event: InputChangeEvent) => void;
  onBlur?: (event: FocusEvent) => void;
  onFocus?: (event: FocusEvent) => void;
  onKeyDown?: (event: KeyboardEvent) => void;
  onKeyUp?: (event: KeyboardEvent) => void;
  onKeyPress?: (event: KeyboardEvent) => void;
}

// Button event types
export interface ButtonEvents {
  onClick: (event: ButtonClickEvent) => void;
  onDoubleClick?: (event: ButtonClickEvent) => void;
  onMouseDown?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseUp?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseEnter?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseLeave?: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

// Modal event types
export interface ModalEvents {
  onOpen?: () => void;
  onClose: () => void;
  onEscape?: () => void;
  onBackdropClick?: () => void;
  onConfirm?: () => void;
  onCancel?: () => void;
}

// Navigation event types
export interface NavigationEvents {
  onNavigate: (path: string, state?: unknown) => void;
  onBack?: () => void;
  onForward?: () => void;
  onRefresh?: () => void;
}

// File upload event types
export interface FileUploadEvents {
  onFileSelect: (files: FileList) => void;
  onUploadStart?: (file: File) => void;
  onUploadProgress?: (file: File, progress: number) => void;
  onUploadComplete?: (file: File, url: string) => void;
  onUploadError?: (file: File, error: string) => void;
  onRemoveFile?: (file: File) => void;
}

// Drag and drop event types
export interface DragDropEvents {
  onDragStart?: (event: React.DragEvent) => void;
  onDragEnd?: (event: React.DragEvent) => void;
  onDragOver?: (event: React.DragEvent) => void;
  onDragEnter?: (event: React.DragEvent) => void;
  onDragLeave?: (event: React.DragEvent) => void;
  onDrop: (event: React.DragEvent) => void;
}

// Search event types
export interface SearchEvents {
  onSearch: (query: string) => void;
  onSearchChange?: (query: string) => void;
  onClearSearch?: () => void;
  onFilterChange?: (filters: Record<string, unknown>) => void;
  onSortChange?: (sortBy: string, direction: 'asc' | 'desc') => void;
}

// Table event types
export interface TableEvents<T> {
  onRowClick?: (item: T, index: number) => void;
  onRowDoubleClick?: (item: T, index: number) => void;
  onRowSelect?: (item: T, selected: boolean) => void;
  onSelectAll?: (selected: boolean) => void;
  onSort?: (column: keyof T, direction: 'asc' | 'desc') => void;
  onFilter?: (column: keyof T, value: unknown) => void;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

// Virtualized list event types
export interface VirtualizedListEvents<T> {
  onItemsRendered?: (startIndex: number, endIndex: number) => void;
  onScroll?: (scrollTop: number, scrollLeft: number) => void;
  onItemClick?: (item: T, index: number) => void;
  onLoadMore?: () => void;
}

// Chart event types
export interface ChartEvents {
  onDataPointClick?: (dataPoint: unknown, index: number) => void;
  onDataPointHover?: (dataPoint: unknown, index: number) => void;
  onLegendClick?: (legendItem: unknown) => void;
  onZoom?: (zoomRange: { start: number; end: number }) => void;
  onReset?: () => void;
}

// WebSocket event types
export interface WebSocketEvents {
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onReconnect?: (attempt: number) => void;
  onMessage?: (message: unknown) => void;
  onError?: (error: Error) => void;
}

// Notification event types
export interface NotificationEvents {
  onShow?: () => void;
  onHide?: () => void;
  onAction?: (action: string) => void;
  onDismiss?: () => void;
  onExpire?: () => void;
}

// Media event types
export interface MediaEvents {
  onPlay?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onSeek?: (position: number) => void;
  onVolumeChange?: (volume: number) => void;
  onMute?: () => void;
  onUnmute?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
}

// Event utilities
export const createEvent = <T extends AppEvent>(
  type: T['type'],
  payload: T['payload'],
  source: BaseEvent['source'] = 'user',
  metadata?: Record<string, unknown>
): T => ({
  type,
  payload,
  timestamp: new Date().toISOString() as Timestamp,
  source,
  metadata,
} as T);

export const isEventType = <T extends AppEvent>(
  event: AppEvent,
  type: T['type']
): event is T => event.type === type;

export const createEventHandler = <T extends AppEvent>(
  handler: (event: T) => void
) => handler;

export const createAsyncEventHandler = <T extends AppEvent>(
  handler: (event: T) => Promise<void>
) => handler;

// Keyboard shortcuts
export type KeyboardShortcut = {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  handler: (event: KeyboardEvent) => void;
  description?: string;
  global?: boolean;
};

export const createKeyboardShortcut = (
  shortcut: KeyboardShortcut
): EventListener<any> => ({
  type: 'keydown' as any,
  handler: (event: any) => {
    const { key, ctrlKey, metaKey, shiftKey, altKey } = event;

    if (
      key === shortcut.key &&
      (shortcut.ctrlKey ?? false) === (ctrlKey ?? false) &&
      (shortcut.metaKey ?? false) === (metaKey ?? false) &&
      (shortcut.shiftKey ?? false) === (shiftKey ?? false) &&
      (shortcut.altKey ?? false) === (altKey ?? false)
    ) {
      event.preventDefault();
      shortcut.handler(event);
    }
  },
});

// Event throttling and debouncing utilities
export const throttle = <T extends (...args: any[]) => void>(
  func: T,
  delay: number
): T => {
  let timeoutId: NodeJS.Timeout | null = null;
  let lastExecTime = 0;

  return ((...args: Parameters<T>) => {
    const currentTime = Date.now();

    if (currentTime - lastExecTime > delay) {
      func(...args);
      lastExecTime = currentTime;
    } else {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        func(...args);
        lastExecTime = Date.now();
      }, delay - (currentTime - lastExecTime));
    }
  }) as T;
};

export const debounce = <T extends (...args: any[]) => void>(
  func: T,
  delay: number
): T => {
  let timeoutId: NodeJS.Timeout | null = null;

  return ((...args: Parameters<T>) => {
    if (timeoutId) clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  }) as T;
};