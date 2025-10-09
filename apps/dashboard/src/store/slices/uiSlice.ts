import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

interface NotificationItem {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  message: string;
  timestamp: number;
  autoHide?: boolean;
  severity?: 'info' | 'warning' | 'success' | 'error';
}

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  language: string;
  notifications: NotificationItem[];
  loading: boolean;
  globalError: string | null;
}

const initialState: UIState = {
  sidebarOpen: true,
  theme: 'light',
  language: 'en',
  notifications: [],
  loading: false,
  globalError: null,
};

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setSidebarOpen(state, action: PayloadAction<boolean>) {
      state.sidebarOpen = action.payload;
    },
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setTheme(state, action: PayloadAction<'light' | 'dark'>) {
      state.theme = action.payload;
    },
    toggleTheme(state) {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
    setLanguage(state, action: PayloadAction<string>) {
      state.language = action.payload;
    },
    addNotification(state, action: PayloadAction<Omit<NotificationItem, 'id' | 'timestamp'>>) {
      const notification: NotificationItem = {
        ...action.payload,
        id: `notification-${Date.now()}-${Math.random()}`,
        timestamp: Date.now(),
      };
      state.notifications.push(notification);
    },
    removeNotification(state, action: PayloadAction<string>) {
      state.notifications = state.notifications.filter((n) => n.id !== action.payload);
    },
    clearNotifications(state) {
      state.notifications = [];
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    setGlobalError(state, action: PayloadAction<string | null>) {
      state.globalError = action.payload;
    },
  },
});

export const {
  setSidebarOpen,
  toggleSidebar,
  setTheme,
  toggleTheme,
  setLanguage,
  addNotification,
  removeNotification,
  clearNotifications,
  setLoading,
  setGlobalError,
} = uiSlice.actions;

export default uiSlice.reducer;