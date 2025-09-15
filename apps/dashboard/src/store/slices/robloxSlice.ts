/**
 * Roblox Redux Slice
 * 
 * State management for all Roblox-related features including:
 * - Plugin connection status
 * - Content generation
 * - Student progress tracking
 * - Session management
 * - Quiz results
 * - Environment preview
 * - Environment management (creation, generation, deployment)
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Import types from sync service
export interface RobloxEnvironment {
  id: string;
  name: string;
  theme: string;
  mapType: string;
  status: 'draft' | 'generating' | 'ready' | 'deployed' | 'error';
  spec: RobloxSpec;
  generatedAt?: string;
  downloadUrl?: string;
  previewUrl?: string;
  userId: string;
  conversationId?: string;
}

export interface RobloxSpec {
  environment_name: string;
  theme: string;
  map_type: 'obby' | 'open_world' | 'dungeon' | 'lab' | 'classroom' | 'puzzle' | 'arena';
  terrain?: string;
  npc_count?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  learning_objectives: string[];
  age_range?: string;
  assets?: string[];
  scripting?: string[];
  lighting?: string;
  weather?: string;
  notes?: string;
}

export interface GenerationStatus {
  environmentId: string;
  status: 'idle' | 'generating' | 'ready' | 'error';
  progress?: number;
  stage?: string;
  message?: string;
  requestId?: string;
  error?: string;
}

// Existing types
interface PluginStatus {
  connected: boolean;
  version?: string;
  lastHeartbeat?: string;
  capabilities?: string[];
}

interface ContentGenerationSession {
  id: string;
  status: 'idle' | 'initializing' | 'processing' | 'reviewing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  agents: {
    [agentId: string]: {
      name: string;
      status: string;
      progress: number;
      currentTask?: string;
      error?: string;
    };
  };
  request?: {
    subject: string;
    gradeLevel: number;
    objectives: string[];
    environmentType: string;
  };
  output?: any;
  startTime?: string;
  endTime?: string;
  errors: string[];
}

interface RobloxSession {
  id: string;
  name: string;
  status: 'draft' | 'ready' | 'active' | 'paused' | 'completed' | 'archived';
  participants: {
    teacherId: string;
    students: Array<{
      id: string;
      name: string;
      status: string;
    }>;
  };
  metrics: {
    totalPlayers: number;
    activePlayers: number;
    averageProgress: number;
    completionRate: number;
  };
}

interface StudentProgress {
  userId: string;
  username: string;
  status: 'online' | 'offline' | 'idle' | 'active';
  progress: {
    overall: number;
    objectives: Array<{
      id: string;
      name: string;
      completed: boolean;
      progress: number;
    }>;
  };
  metrics: {
    engagement: number;
    accuracy: number;
    speed: number;
    collaboration: number;
  };
  lastUpdate: string;
}

interface QuizResult {
  quizId: string;
  quizName: string;
  sessionId: string;
  timestamp: string;
  overallMetrics: {
    averageScore: number;
    passRate: number;
    completionRate: number;
  };
  studentResults: Array<{
    studentId: string;
    studentName: string;
    score: number;
    percentage: number;
  }>;
}

interface Environment {
  id: string;
  name: string;
  type: string;
  status: 'loading' | 'ready' | 'error';
  metadata?: {
    subject: string;
    gradeLevel: number;
    size: { x: number; y: number; z: number };
    polyCount: number;
  };
}

// Combined state interface
interface RobloxState {
  // Plugin connection
  plugin: PluginStatus;

  // Content generation
  contentGeneration: {
    currentSession: ContentGenerationSession | null;
    recentSessions: ContentGenerationSession[];
    isGenerating: boolean;
  };

  // Sessions
  sessions: {
    active: RobloxSession[];
    archived: RobloxSession[];
    currentSession: RobloxSession | null;
  };

  // Student progress
  studentProgress: {
    students: StudentProgress[];
    classMetrics: {
      totalStudents: number;
      activeStudents: number;
      averageProgress: number;
      averageEngagement: number;
    } | null;
  };

  // Quiz results
  quizResults: {
    recent: QuizResult[];
    selected: QuizResult | null;
  };

  // Environment preview
  environment: {
    current: Environment | null;
    previewUrl: string | null;
    isLoading: boolean;
  };

  // Environment management (new)
  environments: RobloxEnvironment[];
  activeEnvironmentId: string | null;
  generationStatus: Record<string, GenerationStatus>;

  // General
  loading: boolean;
  error: string | null;
}

const initialState: RobloxState = {
  plugin: {
    connected: false
  },
  contentGeneration: {
    currentSession: null,
    recentSessions: [],
    isGenerating: false
  },
  sessions: {
    active: [],
    archived: [],
    currentSession: null
  },
  studentProgress: {
    students: [],
    classMetrics: null
  },
  quizResults: {
    recent: [],
    selected: null
  },
  environment: {
    current: null,
    previewUrl: null,
    isLoading: false
  },
  // New environment management state
  environments: [],
  activeEnvironmentId: null,
  generationStatus: {},

  loading: false,
  error: null
};

// Slice
const robloxSlice = createSlice({
  name: 'roblox',
  initialState,
  reducers: {
    // Plugin actions
    setPluginStatus: (state, action: PayloadAction<PluginStatus>) => {
      state.plugin = action.payload;
    },

    updatePluginHeartbeat: (state, action: PayloadAction<string>) => {
      state.plugin.lastHeartbeat = action.payload;
    },

    // Content generation actions
    startContentGeneration: (state, action: PayloadAction<ContentGenerationSession['request']>) => {
      state.contentGeneration.isGenerating = true;
      state.contentGeneration.currentSession = {
        id: `gen_${Date.now()}`,
        status: 'initializing',
        progress: 0,
        agents: {},
        request: action.payload,
        errors: [],
        startTime: new Date().toISOString()
      };
    },

    updateContentProgress: (state, action: PayloadAction<{
      sessionId: string;
      agentId?: string;
      progress: number;
      status?: string;
      currentTask?: string;
    }>) => {
      if (state.contentGeneration.currentSession?.id === action.payload.sessionId) {
        state.contentGeneration.currentSession.progress = action.payload.progress;

        if (action.payload.status) {
          state.contentGeneration.currentSession.status = action.payload.status as any;
        }

        if (action.payload.agentId) {
          if (!state.contentGeneration.currentSession.agents[action.payload.agentId]) {
            state.contentGeneration.currentSession.agents[action.payload.agentId] = {
              name: action.payload.agentId,
              status: 'idle',
              progress: 0
            };
          }

          const agent = state.contentGeneration.currentSession.agents[action.payload.agentId];
          agent.progress = action.payload.progress;
          if (action.payload.status) agent.status = action.payload.status;
          if (action.payload.currentTask) agent.currentTask = action.payload.currentTask;
        }
      }
    },

    completeContentGeneration: (state, action: PayloadAction<{ sessionId: string; output: any }>) => {
      if (state.contentGeneration.currentSession?.id === action.payload.sessionId) {
        state.contentGeneration.currentSession.status = 'completed';
        state.contentGeneration.currentSession.progress = 100;
        state.contentGeneration.currentSession.output = action.payload.output;
        state.contentGeneration.currentSession.endTime = new Date().toISOString();
        state.contentGeneration.isGenerating = false;

        // Add to recent sessions
        state.contentGeneration.recentSessions.unshift(state.contentGeneration.currentSession);
        if (state.contentGeneration.recentSessions.length > 10) {
          state.contentGeneration.recentSessions.pop();
        }
      }
    },

    cancelContentGeneration: (state) => {
      if (state.contentGeneration.currentSession) {
        state.contentGeneration.currentSession.status = 'cancelled';
        state.contentGeneration.currentSession.endTime = new Date().toISOString();
        state.contentGeneration.isGenerating = false;
      }
    },

    // Session actions
    addSession: (state, action: PayloadAction<RobloxSession>) => {
      state.sessions.active.push(action.payload);
    },

    updateSession: (state, action: PayloadAction<RobloxSession>) => {
      const index = state.sessions.active.findIndex(s => s.id === action.payload.id);
      if (index !== -1) {
        state.sessions.active[index] = action.payload;
      }

      if (state.sessions.currentSession?.id === action.payload.id) {
        state.sessions.currentSession = action.payload;
      }
    },

    removeSession: (state, action: PayloadAction<string>) => {
      state.sessions.active = state.sessions.active.filter(s => s.id !== action.payload);
      if (state.sessions.currentSession?.id === action.payload) {
        state.sessions.currentSession = null;
      }
    },

    setCurrentSession: (state, action: PayloadAction<RobloxSession | null>) => {
      state.sessions.currentSession = action.payload;
    },

    archiveSession: (state, action: PayloadAction<string>) => {
      const session = state.sessions.active.find(s => s.id === action.payload);
      if (session) {
        state.sessions.active = state.sessions.active.filter(s => s.id !== action.payload);
        state.sessions.archived.push({ ...session, status: 'archived' });
      }
    },

    // Student progress actions
    updateStudentProgress: (state, action: PayloadAction<StudentProgress>) => {
      const index = state.studentProgress.students.findIndex(s => s.userId === action.payload.userId);
      if (index !== -1) {
        state.studentProgress.students[index] = action.payload;
      } else {
        state.studentProgress.students.push(action.payload);
      }
    },

    updateBulkStudentProgress: (state, action: PayloadAction<StudentProgress[]>) => {
      action.payload.forEach(student => {
        const index = state.studentProgress.students.findIndex(s => s.userId === student.userId);
        if (index !== -1) {
          state.studentProgress.students[index] = student;
        } else {
          state.studentProgress.students.push(student);
        }
      });
    },

    setClassMetrics: (state, action: PayloadAction<typeof initialState.studentProgress.classMetrics>) => {
      state.studentProgress.classMetrics = action.payload;
    },

    clearInactiveStudents: (state) => {
      state.studentProgress.students = state.studentProgress.students.filter(
        s => s.status !== 'offline'
      );
    },

    // Quiz results actions
    addQuizResult: (state, action: PayloadAction<QuizResult>) => {
      state.quizResults.recent.unshift(action.payload);
      if (state.quizResults.recent.length > 20) {
        state.quizResults.recent.pop();
      }
    },

    setSelectedQuizResult: (state, action: PayloadAction<QuizResult | null>) => {
      state.quizResults.selected = action.payload;
    },

    updateQuizResult: (state, action: PayloadAction<QuizResult>) => {
      const index = state.quizResults.recent.findIndex(q => q.quizId === action.payload.quizId);
      if (index !== -1) {
        state.quizResults.recent[index] = action.payload;
      }

      if (state.quizResults.selected?.quizId === action.payload.quizId) {
        state.quizResults.selected = action.payload;
      }
    },

    // Environment preview actions
    setCurrentEnvironment: (state, action: PayloadAction<Environment | null>) => {
      state.environment.current = action.payload;
    },

    setEnvironmentPreviewUrl: (state, action: PayloadAction<string | null>) => {
      state.environment.previewUrl = action.payload;
    },

    setEnvironmentLoading: (state, action: PayloadAction<boolean>) => {
      state.environment.isLoading = action.payload;
    },

    updateEnvironmentStatus: (state, action: PayloadAction<{ id: string; status: Environment['status'] }>) => {
      if (state.environment.current?.id === action.payload.id) {
        state.environment.current.status = action.payload.status;
      }
    },

    // Environment management actions (new)
    setRobloxEnvironments: (state, action: PayloadAction<RobloxEnvironment[]>) => {
      state.environments = action.payload;
      state.loading = false;
      state.error = null;
    },

    addRobloxEnvironment: (state, action: PayloadAction<RobloxEnvironment>) => {
      state.environments.push(action.payload);
    },

    updateRobloxEnvironment: (state, action: PayloadAction<Partial<RobloxEnvironment> & { id: string }>) => {
      const index = state.environments.findIndex(env => env.id === action.payload.id);
      if (index !== -1) {
        state.environments[index] = { ...state.environments[index], ...action.payload };
      }
    },

    removeRobloxEnvironment: (state, action: PayloadAction<string>) => {
      state.environments = state.environments.filter(env => env.id !== action.payload);
      if (state.activeEnvironmentId === action.payload) {
        state.activeEnvironmentId = null;
      }
    },

    setActiveEnvironment: (state, action: PayloadAction<string | null>) => {
      state.activeEnvironmentId = action.payload;
    },

    setGenerationStatus: (state, action: PayloadAction<GenerationStatus>) => {
      state.generationStatus[action.payload.environmentId] = action.payload;
    },

    clearGenerationStatus: (state, action: PayloadAction<string>) => {
      delete state.generationStatus[action.payload];
    },

    // General actions
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },

    clearError: (state) => {
      state.error = null;
    },

    resetRobloxState: () => initialState
  }
});

// Export actions
export const {
  // Plugin
  setPluginStatus,
  updatePluginHeartbeat,

  // Content generation
  startContentGeneration,
  updateContentProgress,
  completeContentGeneration,
  cancelContentGeneration,

  // Sessions
  addSession,
  updateSession,
  removeSession,
  setCurrentSession,
  archiveSession,

  // Student progress
  updateStudentProgress,
  updateBulkStudentProgress,
  setClassMetrics,
  clearInactiveStudents,

  // Quiz results
  addQuizResult,
  setSelectedQuizResult,
  updateQuizResult,

  // Environment preview
  setCurrentEnvironment,
  setEnvironmentPreviewUrl,
  setEnvironmentLoading,
  updateEnvironmentStatus,

  // Environment management (new)
  setRobloxEnvironments,
  addRobloxEnvironment,
  updateRobloxEnvironment,
  removeRobloxEnvironment,
  setActiveEnvironment,
  setGenerationStatus,
  clearGenerationStatus,

  // General
  setLoading,
  setError,
  clearError,
  resetRobloxState
} = robloxSlice.actions;

// Selectors
export const selectPluginStatus = (state: { roblox: RobloxState }) => state.roblox.plugin;
export const selectContentGeneration = (state: { roblox: RobloxState }) => state.roblox.contentGeneration;
export const selectSessions = (state: { roblox: RobloxState }) => state.roblox.sessions;
export const selectStudentProgress = (state: { roblox: RobloxState }) => state.roblox.studentProgress;
export const selectQuizResults = (state: { roblox: RobloxState }) => state.roblox.quizResults;
export const selectEnvironment = (state: { roblox: RobloxState }) => state.roblox.environment;
export const selectRobloxLoading = (state: { roblox: RobloxState }) => state.roblox.loading;
export const selectRobloxError = (state: { roblox: RobloxState }) => state.roblox.error;

// New selectors for environment management
export const selectRobloxEnvironments = (state: { roblox: RobloxState }) => state.roblox.environments;
export const selectActiveEnvironmentId = (state: { roblox: RobloxState }) => state.roblox.activeEnvironmentId;
export const selectGenerationStatus = (state: { roblox: RobloxState }) => state.roblox.generationStatus;

// Export reducer
export default robloxSlice.reducer;