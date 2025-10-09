/**
 * Real-time Redux Slice
 * Manages WebSocket and real-time communication state
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import {
  WebSocketState,
  type WebSocketChannel,
  type ContentGenerationProgress,
  type ContentGenerationResponse,
  type SystemNotification
} from '../../types/websocket';

// User presence status
export interface UserPresence {
  userId: string;
  status: 'online' | 'offline' | 'away';
  lastSeen: Date;
  currentActivity?: string;
}

// Classroom state
export interface ClassroomState {
  classroomId: string;
  teacherId: string;
  studentIds: string[];
  currentLesson?: string;
  isInSession: boolean;
  startedAt?: Date;
}

// Quiz state
export interface QuizState {
  quizId: string;
  status: 'waiting' | 'active' | 'completed';
  currentQuestion?: number;
  totalQuestions?: number;
  participants: string[];
  scores?: Record<string, number>;
}

// Leaderboard entry
export interface LeaderboardEntry {
  userId: string;
  username: string;
  score: number;
  rank: number;
  change: number; // Position change
}

// Real-time slice state
export interface RealtimeState {
  // WebSocket connection
  websocket: {
    state: WebSocketState;
    error: {
      message: string;
      code: string;
      timestamp: Date;
    } | null;
    stats: {
      connected: boolean;
      messagesSent: number;
      messagesReceived: number;
      reconnectAttempts: number;
      latency: number | null;
    };
  };
  
  // Subscriptions
  subscriptions: Record<WebSocketChannel, string>; // channel -> subscriptionId
  
  // Messages
  messages: Array<{
    id: string;
    channel: WebSocketChannel;
    message: any;
    timestamp: Date;
  }>;
  
  // Content generation
  contentGeneration: {
    activeRequests: Record<string, ContentGenerationProgress>; // requestId -> progress
    completedRequests: Record<string, ContentGenerationResponse>; // requestId -> result
  };
  
  // System notifications
  notifications: SystemNotification[];
  unreadNotificationCount: number;
  
  // User presence
  userPresence: Record<string, UserPresence>; // userId -> presence
  
  // Classroom state
  classrooms: Record<string, ClassroomState>; // classroomId -> state
  activeClassroomId: string | null;
  
  // Quiz state
  quizzes: Record<string, QuizState>; // quizId -> state
  activeQuizId: string | null;
  
  // Leaderboard
  leaderboard: {
    global: LeaderboardEntry[];
    classroom: LeaderboardEntry[];
    weekly: LeaderboardEntry[];
    lastUpdated: Date | null;
  };
}

// Initial state
const initialState: RealtimeState = {
  websocket: {
    state: WebSocketState.DISCONNECTED,
    error: null,
    stats: {
      connected: false,
      messagesSent: 0,
      messagesReceived: 0,
      reconnectAttempts: 0,
      latency: null
    }
  },
  subscriptions: {} as Record<WebSocketChannel, string>,
  messages: [],
  contentGeneration: {
    activeRequests: {},
    completedRequests: {}
  },
  notifications: [],
  unreadNotificationCount: 0,
  userPresence: {},
  classrooms: {},
  activeClassroomId: null,
  quizzes: {},
  activeQuizId: null,
  leaderboard: {
    global: [],
    classroom: [],
    weekly: [],
    lastUpdated: null
  }
};

// Create slice
const realtimeSlice = createSlice({
  name: 'realtime',
  initialState,
  reducers: {
    // WebSocket state management
    setWebSocketState: (state, action: PayloadAction<WebSocketState>) => {
      state.websocket.state = action.payload;
      if (action.payload === WebSocketState.CONNECTED) {
        state.websocket.error = null;
      }
    },
    
    setWebSocketError: (state, action: PayloadAction<{ message: string; code: string; timestamp: Date }>) => {
      state.websocket.error = action.payload;
      state.websocket.state = WebSocketState.ERROR;
    },
    
    updateWebSocketStats: (state, action: PayloadAction<Partial<RealtimeState['websocket']['stats']>>) => {
      state.websocket.stats = {
        ...state.websocket.stats,
        ...action.payload
      };
    },
    
    incrementMessagesSent: (state) => {
      state.websocket.stats.messagesSent++;
    },
    
    incrementMessagesReceived: (state) => {
      state.websocket.stats.messagesReceived++;
    },
    
    setLatency: (state, action: PayloadAction<number>) => {
      state.websocket.stats.latency = action.payload;
    },
    
    // Subscription management
    addSubscription: (state, action: PayloadAction<{ channel: WebSocketChannel; subscriptionId: string }>) => {
      state.subscriptions[action.payload.channel] = action.payload.subscriptionId;
    },
    
    removeSubscription: (state, action: PayloadAction<{ subscriptionId: string }>) => {
      const channel = Object.entries(state.subscriptions).find(
        ([_, id]) => id === action.payload.subscriptionId
      )?.[0] as WebSocketChannel | undefined;
      
      if (channel) {
        delete state.subscriptions[channel];
      }
    },
    
    clearSubscriptions: (state) => {
      state.subscriptions = {} as Record<WebSocketChannel, string>;
    },
    
    // Message management
    addRealtimeMessage: (state, action: PayloadAction<{
      channel: WebSocketChannel;
      message: any;
      timestamp: Date;
    }>) => {
      state.messages.unshift({
        id: `${Date.now()}_${Math.random()}`,
        ...action.payload
      });
      
      // Keep only last 100 messages
      if (state.messages.length > 100) {
        state.messages = state.messages.slice(0, 100);
      }
      
      state.websocket.stats.messagesReceived++;
    },
    
    clearMessages: (state) => {
      state.messages = [];
    },
    
    // Content generation management
    updateContentProgress: (state, action: PayloadAction<ContentGenerationProgress>) => {
      state.contentGeneration.activeRequests[action.payload.requestId] = action.payload;
    },
    
    setContentComplete: (state, action: PayloadAction<ContentGenerationResponse>) => {
      const { requestId } = action.payload;
      delete state.contentGeneration.activeRequests[requestId];
      state.contentGeneration.completedRequests[requestId] = action.payload;
    },
    
    clearContentRequest: (state, action: PayloadAction<string>) => {
      delete state.contentGeneration.activeRequests[action.payload];
      delete state.contentGeneration.completedRequests[action.payload];
    },
    
    // System notifications
    addSystemNotification: (state, action: PayloadAction<SystemNotification>) => {
      state.notifications.unshift(action.payload);
      state.unreadNotificationCount++;
      
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    
    markNotificationRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification && !notification.read) {
        notification.read = true;
        state.unreadNotificationCount = Math.max(0, state.unreadNotificationCount - 1);
      }
    },
    
    markAllNotificationsRead: (state) => {
      state.notifications.forEach(n => { n.read = true; });
      state.unreadNotificationCount = 0;
    },
    
    clearNotifications: (state) => {
      state.notifications = [];
      state.unreadNotificationCount = 0;
    },
    
    // User presence management
    updateUserPresence: (state, action: PayloadAction<UserPresence>) => {
      state.userPresence[action.payload.userId] = action.payload;
    },
    
    removeUserPresence: (state, action: PayloadAction<string>) => {
      delete state.userPresence[action.payload];
    },
    
    clearUserPresence: (state) => {
      state.userPresence = {};
    },
    
    // Classroom management
    updateClassroomState: (state, action: PayloadAction<ClassroomState>) => {
      state.classrooms[action.payload.classroomId] = action.payload;
    },
    
    setActiveClassroom: (state, action: PayloadAction<string | null>) => {
      state.activeClassroomId = action.payload;
    },
    
    removeClassroom: (state, action: PayloadAction<string>) => {
      delete state.classrooms[action.payload];
      if (state.activeClassroomId === action.payload) {
        state.activeClassroomId = null;
      }
    },
    
    // Quiz management
    updateQuizState: (state, action: PayloadAction<QuizState>) => {
      state.quizzes[action.payload.quizId] = action.payload;
    },
    
    setActiveQuiz: (state, action: PayloadAction<string | null>) => {
      state.activeQuizId = action.payload;
    },
    
    removeQuiz: (state, action: PayloadAction<string>) => {
      delete state.quizzes[action.payload];
      if (state.activeQuizId === action.payload) {
        state.activeQuizId = null;
      }
    },
    
    // Leaderboard management
    updateLeaderboard: (state, action: PayloadAction<{
      type: 'global' | 'classroom' | 'weekly';
      entries: LeaderboardEntry[];
    }>) => {
      state.leaderboard[action.payload.type] = action.payload.entries;
      state.leaderboard.lastUpdated = new Date();
    },
    
    clearLeaderboard: (state) => {
      state.leaderboard = {
        global: [],
        classroom: [],
        weekly: [],
        lastUpdated: null
      };
    },
    
    // Reset all real-time state
    resetRealtimeState: () => initialState
  }
});

// Export actions
export const {
  setWebSocketState,
  setWebSocketError,
  updateWebSocketStats,
  incrementMessagesSent,
  incrementMessagesReceived,
  setLatency,
  addSubscription,
  removeSubscription,
  clearSubscriptions,
  addRealtimeMessage,
  clearMessages,
  updateContentProgress,
  setContentComplete,
  clearContentRequest,
  addSystemNotification,
  markNotificationRead,
  markAllNotificationsRead,
  clearNotifications,
  updateUserPresence,
  removeUserPresence,
  clearUserPresence,
  updateClassroomState,
  setActiveClassroom,
  removeClassroom,
  updateQuizState,
  setActiveQuiz,
  removeQuiz,
  updateLeaderboard,
  clearLeaderboard,
  resetRealtimeState
} = realtimeSlice.actions;

// Export reducer
export default realtimeSlice.reducer;

// Selectors
export const selectWebSocketState = (state: { realtime: RealtimeState }) => state.realtime.websocket.state;
export const selectIsConnected = (state: { realtime: RealtimeState }) => state.realtime.websocket.state === WebSocketState.CONNECTED;
export const selectWebSocketError = (state: { realtime: RealtimeState }) => state.realtime.websocket.error;
export const selectWebSocketStats = (state: { realtime: RealtimeState }) => state.realtime.websocket.stats;
export const selectSubscriptions = (state: { realtime: RealtimeState }) => state.realtime.subscriptions;
export const selectRealtimeMessages = (state: { realtime: RealtimeState }) => state.realtime.messages;
export const selectContentGeneration = (state: { realtime: RealtimeState }) => state.realtime.contentGeneration;
export const selectNotifications = (state: { realtime: RealtimeState }) => state.realtime.notifications;
export const selectUnreadNotificationCount = (state: { realtime: RealtimeState }) => state.realtime.unreadNotificationCount;
export const selectUserPresence = (state: { realtime: RealtimeState }) => state.realtime.userPresence;
export const selectActiveClassroom = (state: { realtime: RealtimeState }) => {
  const id = state.realtime.activeClassroomId;
  return id ? state.realtime.classrooms[id] : null;
};
export const selectActiveQuiz = (state: { realtime: RealtimeState }) => {
  const id = state.realtime.activeQuizId;
  return id ? state.realtime.quizzes[id] : null;
};
export const selectLeaderboard = (state: { realtime: RealtimeState }) => state.realtime.leaderboard;