import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Badge, LeaderboardEntry, XPTransaction } from "../../types/api";

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