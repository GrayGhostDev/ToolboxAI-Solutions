import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import { Badge, LeaderboardEntry, XPTransaction } from "../../types/api";
import * as api from "../../services/api";

interface GamificationState {
  xp: number;
  level: number;
  nextLevelXP: number;
  badges: Badge[];
  leaderboard: LeaderboardEntry[];
  recentXPTransactions: XPTransaction[];
  streakDays: number;
  rank?: number;
  loading: boolean;
  error: string | null;
}

const initialState: GamificationState = {
  xp: 0,
  level: 1,
  nextLevelXP: 100,
  badges: [],
  leaderboard: [],
  recentXPTransactions: [],
  streakDays: 0,
  rank: undefined,
  loading: false,
  error: null,
};

// Async thunks
export const fetchLeaderboard = createAsyncThunk(
  'gamification/fetchLeaderboard',
  async ({ classId, timeframe }: { classId?: string; timeframe?: 'daily' | 'weekly' | 'monthly' | 'all' }) => {
    const response = await api.getLeaderboard(classId, timeframe);
    return response;
  }
);

export const fetchStudentXP = createAsyncThunk(
  'gamification/fetchStudentXP',
  async (studentId: string) => {
    const response = await api.getStudentXP(studentId);
    return response;
  }
);

export const fetchBadges = createAsyncThunk(
  'gamification/fetchBadges',
  async (studentId?: string) => {
    const response = await api.getBadges(studentId);
    return response;
  }
);

export const awardBadgeToStudent = createAsyncThunk(
  'gamification/awardBadge',
  async ({ studentId, badgeId }: { studentId: string; badgeId: string }) => {
    const response = await api.awardBadge(studentId, badgeId);
    return response;
  }
);

export const addXPToStudent = createAsyncThunk(
  'gamification/addXPToStudent',
  async ({ studentId, amount, reason }: { studentId: string; amount: number; reason: string }) => {
    const response = await api.addXP(studentId, amount, reason);
    return response;
  }
);

const gamificationSlice = createSlice({
  name: "gamification",
  initialState,
  reducers: {
    setXP(state, action: PayloadAction<number>) {
      state.xp = action.payload;
      // Calculate level based on XP
      state.level = Math.floor(state.xp / 100) + 1;
      state.nextLevelXP = state.level * 100;
    },
    addXP(state, action: PayloadAction<{ amount: number; reason: string; source: string }>) {
      state.xp += action.payload.amount;
      state.level = Math.floor(state.xp / 100) + 1;
      state.nextLevelXP = state.level * 100;
      
      // Add transaction to recent list
      const transaction: XPTransaction = {
        id: `xp-${Date.now()}`,
        studentId: "", // Will be filled by the app
        amount: action.payload.amount,
        reason: action.payload.reason,
        source: action.payload.source as any,
        timestamp: new Date().toISOString(),
      };
      state.recentXPTransactions = [transaction, ...state.recentXPTransactions].slice(0, 10);
    },
    setBadges(state, action: PayloadAction<Badge[]>) {
      state.badges = action.payload;
    },
    addBadge(state, action: PayloadAction<Badge>) {
      const badge = { ...action.payload, earnedAt: new Date().toISOString() };
      state.badges.push(badge);
    },
    setLeaderboard(state, action: PayloadAction<LeaderboardEntry[]>) {
      state.leaderboard = action.payload;
    },
    setRank(state, action: PayloadAction<number>) {
      state.rank = action.payload;
    },
    setStreakDays(state, action: PayloadAction<number>) {
      state.streakDays = action.payload;
    },
    setRecentTransactions(state, action: PayloadAction<XPTransaction[]>) {
      state.recentXPTransactions = action.payload;
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    resetGamification(state) {
      Object.assign(state, initialState);
    },
  },
  extraReducers: (builder) => {
    // Fetch leaderboard
    builder
      .addCase(fetchLeaderboard.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLeaderboard.fulfilled, (state, action) => {
        state.loading = false;
        state.leaderboard = action.payload;
      })
      .addCase(fetchLeaderboard.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch leaderboard';
      });

    // Fetch student XP
    builder
      .addCase(fetchStudentXP.fulfilled, (state, action) => {
        state.xp = action.payload.xp;
        state.level = action.payload.level;
        state.nextLevelXP = state.level * 100;
      });

    // Fetch badges
    builder
      .addCase(fetchBadges.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchBadges.fulfilled, (state, action) => {
        state.loading = false;
        state.badges = action.payload;
      })
      .addCase(fetchBadges.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch badges';
      });

    // Award badge
    builder
      .addCase(awardBadgeToStudent.fulfilled, (state, action) => {
        state.badges.push(action.payload);
      });

    // Add XP
    builder
      .addCase(addXPToStudent.fulfilled, (state, action) => {
        const transaction = action.payload as XPTransaction;
        state.xp += transaction.amount;
        state.level = Math.floor(state.xp / 100) + 1;
        state.nextLevelXP = state.level * 100;
        state.recentXPTransactions = [transaction, ...state.recentXPTransactions].slice(0, 10);
      });
  },
});

export const {
  setXP,
  addXP,
  setBadges,
  addBadge,
  setLeaderboard,
  setRank,
  setStreakDays,
  setRecentTransactions,
  setLoading,
  setError,
  resetGamification,
} = gamificationSlice.actions;

export default gamificationSlice.reducer;