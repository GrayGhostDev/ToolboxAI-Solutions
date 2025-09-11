import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { DashboardMetrics, Activity, Event } from "../../types/api";

interface DashboardState {
  loading: boolean;
  error: string | null;
  metrics: DashboardMetrics | null;
  recentActivity: Activity[];
  upcomingEvents: Event[];
  lastUpdated: string | null;
}

const initialState: DashboardState = {
  loading: false,
  error: null,
  metrics: null,
  recentActivity: [],
  upcomingEvents: [],
  lastUpdated: null,
};

const dashboardSlice = createSlice({
  name: "dashboard",
  initialState,
  reducers: {
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    setMetrics(state, action: PayloadAction<DashboardMetrics>) {
      state.metrics = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    updateMetric(state, action: PayloadAction<{ key: keyof DashboardMetrics; value: any }>) {
      if (state.metrics) {
        (state.metrics as any)[action.payload.key] = action.payload.value;
      }
    },
    setRecentActivity(state, action: PayloadAction<Activity[]>) {
      state.recentActivity = action.payload;
    },
    addActivity(state, action: PayloadAction<Activity>) {
      state.recentActivity = [action.payload, ...state.recentActivity].slice(0, 20);
    },
    setUpcomingEvents(state, action: PayloadAction<Event[]>) {
      state.upcomingEvents = action.payload;
    },
    addEvent(state, action: PayloadAction<Event>) {
      state.upcomingEvents.push(action.payload);
      // Sort by date
      state.upcomingEvents.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    },
    removeEvent(state, action: PayloadAction<string>) {
      state.upcomingEvents = state.upcomingEvents.filter((e) => e.id !== action.payload);
    },
    resetDashboard(state) {
      Object.assign(state, initialState);
    },
  },
});

export const {
  setLoading,
  setError,
  setMetrics,
  updateMetric,
  setRecentActivity,
  addActivity,
  setUpcomingEvents,
  addEvent,
  removeEvent,
  resetDashboard,
} = dashboardSlice.actions;

export default dashboardSlice.reducer;